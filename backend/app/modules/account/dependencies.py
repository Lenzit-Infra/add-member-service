# app/modules/account/dependencies.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.core.permissions import role_has_permission, FIXED_ADMIN_ONLY
from app.repositories.settings_repo import SettingsRepository
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


def require_permission(permission: str):
    """Route-level dependency for mutating endpoints. Admin always passes;
    operator/viewer are checked against their stored permission set (fixed
    admin-only permissions like users.manage always 403 for non-admins)."""

    def checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if current_user.role == "admin":
            return current_user
        granted = set()
        if permission not in FIXED_ADMIN_ONLY:
            settings_repo = SettingsRepository(db)
            settings_repo.initialize_defaults()  # self-healing, same as AccountService — guarantees role defaults exist
            granted = settings_repo.get_role_permissions(current_user.role)
        if not role_has_permission(current_user.role, permission, granted):
            raise HTTPException(status_code=403, detail="You don't have permission to do this.")
        return current_user

    return checker
