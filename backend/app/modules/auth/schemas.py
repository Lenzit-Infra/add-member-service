from pydantic import BaseModel

class LoginRequest(BaseModel):
    phone: str
    api_id: str
    api_hash: str

class VerifyCodeRequest(BaseModel):
    phone: str
    code: str
    phone_code_hash: str

class VerifyPasswordRequest(BaseModel):
    phone: str
    password: str