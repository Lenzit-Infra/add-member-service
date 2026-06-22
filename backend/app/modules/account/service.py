# app/modules/account/service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.user import User
from app.core import security, config
from app.core.email_utils import send_email
from app.core.permissions import ROLES, PERMISSION_CATALOG, DEFAULT_ROLE_PERMISSIONS
from app.repositories.settings_repo import SettingsRepository
from app.services import audit


class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = SettingsRepository(db)
        # Self-healing: guarantees admin_emails (and every other tunable)
        # exists before it's read, regardless of whether anyone has opened
        # the Settings page yet — this is the very first thing a fresh
        # deployment needs to work.
        self.settings.initialize_defaults()

    def _setting_int(self, key: str, default: int) -> int:
        return int(self.settings.get_setting(key, str(default)))

    # --- Login ---

    def authenticate(self, username_or_email: str, password: str, client_ip: str = None) -> User:
        identifier = username_or_email.strip().lower()
        user = self.db.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user.locked_until and user.locked_until > datetime.utcnow():
            minutes_left = max(1, int((user.locked_until - datetime.utcnow()).total_seconds() // 60))
            raise HTTPException(status_code=423, detail=f"Account locked. Try again in {minutes_left} minute(s).")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        max_failed = self._setting_int("login_max_failed_attempts", 5)
        lockout_minutes = self._setting_int("login_lockout_minutes", 15)

        if not security.verify_password(password, user.password_hash):
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= max_failed:
                user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
                user.failed_attempts = 0
            self.db.commit()
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        self.db.commit()
        return user

    # --- Admin claim ---

    def request_claim(self, email: str):
        email = email.strip().lower()
        eligible = email in self.settings.get_admin_emails()
        already_claimed = self.db.query(User).filter(User.email == email).first() is not None

        if eligible and not already_claimed:
            expire_minutes = self._setting_int("claim_token_expire_minutes", 30)
            token = security.create_claim_token(email, expire_minutes)
            # Query-param routing (not a path) so this works on static hosting
            # (GitHub Pages) with zero server-side route configuration.
            link = f"{config.FRONTEND_URL}/?view=claim-admin&token={token}"
            send_email(
                email,
                "Claim your Lenzit dashboard admin account",
                f"<p>Click below to finish setting up your admin account:</p><p><a href='{link}'>{link}</a></p>"
                f"<p>This link expires in {expire_minutes} minutes.</p>",
            )
        # Always the same response — don't leak which emails are valid admin emails.

    def complete_claim(self, token: str, username: str, password: str) -> User:
        payload = security.decode_token_of_type(token, "claim")
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid or expired claim link")

        email = payload["email"]
        if email not in self.settings.get_admin_emails():
            raise HTTPException(status_code=403, detail="This email is no longer eligible")

        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="This account has already been claimed")

        username = username.strip().lower()
        if self.db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=409, detail="Username already taken")

        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        user = User(
            username=username,
            email=email,
            password_hash=security.hash_password(password),
            role="admin",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # --- Forgot / reset password ---

    def request_password_reset(self, email: str):
        email = email.strip().lower()
        user = self.db.query(User).filter(User.email == email).first()

        if user:
            expire_minutes = self._setting_int("reset_token_expire_minutes", 30)
            token = security.create_reset_token(user.id, user.token_version, expire_minutes)
            link = f"{config.FRONTEND_URL}/?view=reset-password&token={token}"
            send_email(
                email,
                "Reset your Lenzit dashboard password",
                f"<p>Click below to reset your password:</p><p><a href='{link}'>{link}</a></p>"
                f"<p>This link expires in {expire_minutes} minutes. "
                f"If you didn't request this, you can ignore this email.</p>",
            )
        # Always the same response — don't leak which emails have accounts.

    def reset_password(self, token: str, new_password: str):
        payload = security.decode_token_of_type(token, "reset")
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid or expired reset link")

        user = self.db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user or user.token_version != payload["tv"]:
            raise HTTPException(status_code=400, detail="Invalid or expired reset link")

        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        user.password_hash = security.hash_password(new_password)
        user.token_version += 1  # invalidates every outstanding refresh/reset token
        user.failed_attempts = 0
        user.locked_until = None
        self.db.commit()

    # --- User management (admin-only, gated at the route level) ---

    def _remaining_admin_count(self, excluding_user_id: int = None) -> int:
        q = self.db.query(User).filter(User.role == "admin", User.is_active == True)
        if excluding_user_id is not None:
            q = q.filter(User.id != excluding_user_id)
        return q.count()

    def list_users(self) -> list:
        return self.db.query(User).order_by(User.created_at.asc()).all()

    def create_user(self, username: str, email: str, password: str, role: str, actor_username: str) -> User:
        username = username.strip().lower()
        email = email.strip().lower()
        if role not in ROLES:
            raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ROLES)}")
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        if self.db.query(User).filter(or_(User.username == username, User.email == email)).first():
            raise HTTPException(status_code=409, detail="A user with that username or email already exists")

        user = User(username=username, email=email, password_hash=security.hash_password(password), role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        audit.log_action(self.db, actor_username, "user.create", f"user:{username}", f"role={role}")
        return user

    def update_user(self, user_id: int, actor: User, role: str = None, is_active: bool = None, new_password: str = None) -> User:
        target = self.db.query(User).filter(User.id == user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")

        demoting_or_disabling_last_admin = (
            target.role == "admin"
            and ((role is not None and role != "admin") or (is_active is False))
            and self._remaining_admin_count(excluding_user_id=target.id) == 0
        )
        if demoting_or_disabling_last_admin:
            raise HTTPException(status_code=400, detail="Can't demote or disable the last remaining admin")

        if role is not None:
            if role not in ROLES:
                raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(ROLES)}")
            if role != target.role:
                audit.log_action(self.db, actor.username, "user.role_change", f"user:{target.username}", f"{target.role} -> {role}")
            target.role = role

        if is_active is not None and is_active != target.is_active:
            target.is_active = is_active
            audit.log_action(self.db, actor.username, "user.activation_change", f"user:{target.username}", f"is_active={is_active}")

        if new_password is not None:
            if len(new_password) < 8:
                raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
            target.password_hash = security.hash_password(new_password)
            target.token_version += 1
            target.failed_attempts = 0
            target.locked_until = None
            audit.log_action(self.db, actor.username, "user.password_reset", f"user:{target.username}")

        self.db.commit()
        self.db.refresh(target)
        return target

    def delete_user(self, user_id: int, actor: User):
        target = self.db.query(User).filter(User.id == user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if target.id == actor.id:
            raise HTTPException(status_code=400, detail="You can't delete your own account")
        if target.role == "admin" and self._remaining_admin_count(excluding_user_id=target.id) == 0:
            raise HTTPException(status_code=400, detail="Can't delete the last remaining admin")

        username = target.username
        self.db.delete(target)
        self.db.commit()
        audit.log_action(self.db, actor.username, "user.delete", f"user:{username}")

    # --- Roles & permissions ---

    def list_roles(self) -> dict:
        roles = {}
        for role in ROLES:
            if role == "admin":
                roles[role] = {"permissions": [p["key"] for p in PERMISSION_CATALOG], "fixed": True}
            else:
                roles[role] = {"permissions": sorted(self.settings.get_role_permissions(role)), "fixed": False}
        return {"catalog": PERMISSION_CATALOG, "roles": roles}

    def set_role_permissions(self, role: str, permissions: list, actor_username: str) -> set:
        if role == "admin":
            raise HTTPException(status_code=400, detail="The admin role's permissions are fixed and can't be edited")
        try:
            updated = self.settings.set_role_permissions(role, permissions)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        audit.log_action(self.db, actor_username, "role.permissions_update", f"role:{role}", ",".join(sorted(updated)))
        return updated
