# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base


class User(Base):
    """Dashboard login account (separate from Agent, which is a Telegram bot account)."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")
    is_active = Column(Boolean, default=True)

    # Bumped on password reset — invalidates every outstanding refresh/reset token at once.
    token_version = Column(Integer, default=0)

    # Brute-force lockout
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
