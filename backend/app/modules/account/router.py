# app/modules/account/router.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security, config
from app.models.user import User
from app.repositories.settings_repo import SettingsRepository
from app.services import audit
from .schemas import (
    LoginRequest, ClaimAdminRequest, ClaimAdminComplete, ForgotPasswordRequest, ResetPasswordRequest,
    CreateUserRequest, UpdateUserRequest, RolePermissionsUpdate,
)
from .service import AccountService
from .dependencies import get_current_user, require_permission

router = APIRouter()


def _client_ip(request: Request) -> str:
    # Traffic arrives via the Cloudflare Tunnel — prefer the header Cloudflare
    # sets to the real visitor IP over the tunnel's local connection address.
    return request.headers.get("CF-Connecting-IP") or (request.client.host if request.client else None)

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/account"


def _set_refresh_cookie(response: Response, user: User, db: Session):
    days = int(SettingsRepository(db).get_setting("refresh_token_expire_days", str(config.REFRESH_TOKEN_EXPIRE_DAYS)))
    token = security.create_refresh_token(user.id, user.token_version, expire_days=days)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="lax",
        domain=config.COOKIE_DOMAIN,
        path=REFRESH_COOKIE_PATH,
        max_age=days * 86400,
    )


def _create_access_token(user: User, db: Session) -> str:
    minutes = int(SettingsRepository(db).get_setting("access_token_expire_minutes", str(config.ACCESS_TOKEN_EXPIRE_MINUTES)))
    return security.create_access_token(user.id, expire_minutes=minutes)


def _user_public(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}


@router.post("/login")
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    service = AccountService(db)
    user = service.authenticate(data.username_or_email, data.password, client_ip=_client_ip(request))
    _set_refresh_cookie(response, user, db)
    return {"access_token": _create_access_token(user, db), "user": _user_public(user)}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh session")

    payload = security.decode_token_of_type(token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active or user.token_version != payload["tv"]:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")

    _set_refresh_cookie(response, user, db)  # rotate
    return {"access_token": _create_access_token(user, db), "user": _user_public(user)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, domain=config.COOKIE_DOMAIN, path=REFRESH_COOKIE_PATH)
    return {"status": "success"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return _user_public(current_user)


@router.post("/claim-admin/request")
def claim_admin_request(data: ClaimAdminRequest, db: Session = Depends(get_db)):
    AccountService(db).request_claim(data.email)
    return {"status": "success", "message": "If that email is eligible, a claim link has been sent."}


@router.post("/claim-admin/complete")
def claim_admin_complete(data: ClaimAdminComplete, response: Response, db: Session = Depends(get_db)):
    service = AccountService(db)
    user = service.complete_claim(data.token, data.username, data.password)
    _set_refresh_cookie(response, user, db)
    return {"access_token": _create_access_token(user, db), "user": _user_public(user)}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AccountService(db).request_password_reset(data.email)
    return {"status": "success", "message": "If that email has an account, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    AccountService(db).reset_password(data.token, data.new_password)
    return {"status": "success", "message": "Password updated. You can now log in."}


def _user_full(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_login_ip": user.last_login_ip,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
    }


@router.get("/users", dependencies=[Depends(require_permission("users.manage"))])
def list_users(db: Session = Depends(get_db)):
    return [_user_full(u) for u in AccountService(db).list_users()]


@router.post("/users", dependencies=[Depends(require_permission("users.manage"))])
def create_user(data: CreateUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = AccountService(db).create_user(data.username, data.email, data.password, data.role, current_user.username)
    return _user_full(user)


@router.patch("/users/{user_id}", dependencies=[Depends(require_permission("users.manage"))])
def update_user(user_id: int, data: UpdateUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = AccountService(db).update_user(
        user_id, current_user, role=data.role, is_active=data.is_active, new_password=data.new_password
    )
    return _user_full(user)


@router.delete("/users/{user_id}", dependencies=[Depends(require_permission("users.manage"))])
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AccountService(db).delete_user(user_id, current_user)
    return {"status": "success", "id": user_id}


@router.get("/roles", dependencies=[Depends(require_permission("roles.manage"))])
def list_roles(db: Session = Depends(get_db)):
    return AccountService(db).list_roles()


@router.post("/roles/{role}/permissions", dependencies=[Depends(require_permission("roles.manage"))])
def update_role_permissions(role: str, data: RolePermissionsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = AccountService(db).set_role_permissions(role, data.permissions, current_user.username)
    return {"role": role, "permissions": sorted(updated)}


def _audit_entry(a) -> dict:
    return {
        "id": a.id,
        "actor_username": a.actor_username,
        "action": a.action,
        "target": a.target,
        "details": a.details,
        "timestamp": a.timestamp.isoformat() if a.timestamp else None,
    }


@router.get("/audit-log", dependencies=[Depends(require_permission("users.manage"))])
def get_audit_log(
    actor: str = None,
    action: str = None,
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db),
):
    parsed_from = datetime.fromisoformat(date_from) if date_from else None
    parsed_to = datetime.fromisoformat(date_to) if date_to else None
    items, total = audit.search(db, actor=actor, action=action, date_from=parsed_from, date_to=parsed_to, page=page, page_size=page_size)
    return {
        "items": [_audit_entry(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit-log/actions", dependencies=[Depends(require_permission("users.manage"))])
def get_audit_log_actions(db: Session = Depends(get_db)):
    return {"actions": audit.list_actions(db)}
