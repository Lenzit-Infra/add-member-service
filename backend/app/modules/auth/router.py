from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from .schemas import LoginRequest, VerifyCodeRequest
from .service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/request-code")
async def request_code(data: LoginRequest):
    try:
        hash_code = await auth_service.initiate_login(data.phone, data.api_id, data.api_hash)
        if not hash_code:
            return {"status": "error", "message": "Already authorized"}
        return {"status": "success", "phone_code_hash": hash_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    try:
        await auth_service.verify_code(data.phone, data.code, db)
        return {"status": "success", "message": "Agent Added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))