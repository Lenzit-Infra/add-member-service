# app/core/security.py
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core import config


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _encode(payload: dict) -> str:
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def _decode(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def create_access_token(user_id: int, expire_minutes: Optional[int] = None) -> str:
    minutes = expire_minutes if expire_minutes is not None else config.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": str(user_id),  # PyJWT requires "sub" to be a string
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    })


def create_refresh_token(user_id: int, token_version: int, expire_days: Optional[int] = None) -> str:
    days = expire_days if expire_days is not None else config.REFRESH_TOKEN_EXPIRE_DAYS
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": str(user_id),
        "type": "refresh",
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(days=days),
    })


def create_claim_token(email: str, expire_minutes: Optional[int] = None) -> str:
    minutes = expire_minutes if expire_minutes is not None else config.CLAIM_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    return _encode({
        "email": email.lower(),
        "type": "claim",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    })


def create_reset_token(user_id: int, token_version: int, expire_minutes: Optional[int] = None) -> str:
    minutes = expire_minutes if expire_minutes is not None else config.RESET_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": str(user_id),
        "type": "reset",
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    })


def decode_token_of_type(token: str, expected_type: str) -> Optional[dict]:
    """Decodes a token and returns its payload only if it's valid, unexpired,
    and matches the expected `type` claim. Returns None on any mismatch."""
    payload = _decode(token)
    if not payload or payload.get("type") != expected_type:
        return None
    return payload
