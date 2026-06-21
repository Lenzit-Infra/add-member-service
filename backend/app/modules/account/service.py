# app/modules/account/service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.user import User
from app.core import security, config
from app.core.email_utils import send_email

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    # --- Login ---

    def authenticate(self, username_or_email: str, password: str) -> User:
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

        if not security.verify_password(password, user.password_hash):
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_attempts = 0
            self.db.commit()
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        return user

    # --- Admin claim ---

    def request_claim(self, email: str):
        email = email.strip().lower()
        eligible = email in config.ADMIN_EMAILS
        already_claimed = self.db.query(User).filter(User.email == email).first() is not None

        if eligible and not already_claimed:
            token = security.create_claim_token(email)
            # Query-param routing (not a path) so this works on static hosting
            # (GitHub Pages) with zero server-side route configuration.
            link = f"{config.FRONTEND_URL}/?view=claim-admin&token={token}"
            send_email(
                email,
                "Claim your Lenzit dashboard admin account",
                f"<p>Click below to finish setting up your admin account:</p><p><a href='{link}'>{link}</a></p>"
                f"<p>This link expires in {config.CLAIM_TOKEN_EXPIRE_MINUTES} minutes.</p>",
            )
        # Always the same response — don't leak which emails are valid admin emails.

    def complete_claim(self, token: str, username: str, password: str) -> User:
        payload = security.decode_token_of_type(token, "claim")
        if not payload:
            raise HTTPException(status_code=400, detail="Invalid or expired claim link")

        email = payload["email"]
        if email not in config.ADMIN_EMAILS:
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
            token = security.create_reset_token(user.id, user.token_version)
            link = f"{config.FRONTEND_URL}/?view=reset-password&token={token}"
            send_email(
                email,
                "Reset your Lenzit dashboard password",
                f"<p>Click below to reset your password:</p><p><a href='{link}'>{link}</a></p>"
                f"<p>This link expires in {config.RESET_TOKEN_EXPIRE_MINUTES} minutes. "
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
