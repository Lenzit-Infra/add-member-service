# app/modules/health/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import health

router = APIRouter()


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """Public, unauthenticated — the dashboard polls this to show a live
    backend/worker/Telegram-reachability status indicator."""
    return health.get_status(db)
