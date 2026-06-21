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
