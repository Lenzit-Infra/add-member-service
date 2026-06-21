# app/modules/account/router.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security, config
from app.models.user import User
from .schemas import LoginRequest, ClaimAdminRequest, ClaimAdminComplete, ForgotPasswordRequest, ResetPasswordRequest
from .service import AccountService
from .dependencies import get_current_user

router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/account"


def _set_refresh_cookie(response: Response, user: User):
    token = security.create_refresh_token(user.id, user.token_version)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="lax",
        domain=config.COOKIE_DOMAIN,
        path=REFRESH_COOKIE_PATH,
        max_age=config.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _user_public(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    service = AccountService(db)
    user = service.authenticate(data.username_or_email, data.password)
    _set_refresh_cookie(response, user)
    return {"access_token": security.create_access_token(user.id), "user": _user_public(user)}


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

    _set_refresh_cookie(response, user)  # rotate
    return {"access_token": security.create_access_token(user.id), "user": _user_public(user)}


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
    _set_refresh_cookie(response, user)
    return {"access_token": security.create_access_token(user.id), "user": _user_public(user)}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AccountService(db).request_password_reset(data.email)
    return {"status": "success", "message": "If that email has an account, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    AccountService(db).reset_password(data.token, data.new_password)
    return {"status": "success", "message": "Password updated. You can now log in."}
