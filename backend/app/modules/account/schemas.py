from typing import List, Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class ClaimAdminRequest(BaseModel):
    email: EmailStr


class ClaimAdminComplete(BaseModel):
    token: str
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None


class RolePermissionsUpdate(BaseModel):
    permissions: List[str]
