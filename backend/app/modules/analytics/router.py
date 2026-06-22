from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.settings_schema import SETTINGS_SCHEMA
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.settings_repo import SettingsRepository
from .schemas import SettingUpdate


class AdminEmailRequest(BaseModel):
    email: EmailStr

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return {
        "agents": repo.get_agent_performance_summary(),
        "totals": repo.get_summary_totals(),
        "trend": repo.get_daily_adds_trend(days=7),
    }

@router.get("/members")
def get_members(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_all_members()

@router.get("/groups")
def get_groups(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_all_groups()

@router.get("/movements")
def get_movements(group_id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_movements(group_id=group_id)

@router.get("/capacity")
def get_capacity(db: Session = Depends(get_db)):
    """Backs the Dashboard's capacity-planning panel: per-order blocking
    reason + ETA, plus portfolio-level agents-needed/days-to-clear."""
    repo = AnalyticsRepository(db)
    return repo.get_capacity_planning()

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """Every tunable, enriched with its category/label/description so the
    Settings page can group and render without duplicating that metadata."""
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    return [
        {**schema_entry, "value": repo.get_setting(schema_entry["key"], str(schema_entry["default"]))}
        for schema_entry in SETTINGS_SCHEMA
    ]

@router.post("/settings")
def update_setting(data: SettingUpdate, db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.set_setting(data.key, data.value)
    return {"status": "success", "key": data.key, "value": data.value}

@router.get("/admin-emails")
def get_admin_emails(db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    return {"emails": repo.get_admin_emails()}

@router.post("/admin-emails")
def add_admin_email(data: AdminEmailRequest, db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    return {"emails": repo.add_admin_email(data.email)}

@router.delete("/admin-emails/{email}")
def remove_admin_email(email: str, db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    try:
        return {"emails": repo.remove_admin_email(email)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
