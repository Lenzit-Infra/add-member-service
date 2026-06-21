# app/modules/account/dependencies.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models.user import User


def get_current_user(authorization: str = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization[len("Bearer "):].strip()
    payload = security.decode_token_of_type(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
