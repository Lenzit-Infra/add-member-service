from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.settings_schema import SETTINGS_SCHEMA
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.settings_repo import SettingsRepository
from app.modules.account.dependencies import get_current_user, require_permission
from app.models.user import User
from app.services import audit
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

@router.post("/settings", dependencies=[Depends(require_permission("settings.manage"))])
def update_setting(data: SettingUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.set_setting(data.key, data.value)
    audit.log_action(db, current_user.username, "settings.update", f"setting:{data.key}", f"value={data.value}")
    return {"status": "success", "key": data.key, "value": data.value}

@router.get("/admin-emails", dependencies=[Depends(require_permission("admin_emails.manage"))])
def get_admin_emails(db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    return {"emails": repo.get_admin_emails()}

@router.post("/admin-emails", dependencies=[Depends(require_permission("admin_emails.manage"))])
def add_admin_email(data: AdminEmailRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    emails = repo.add_admin_email(data.email)
    audit.log_action(db, current_user.username, "admin_email.add", f"email:{data.email}")
    return {"emails": emails}

@router.delete("/admin-emails/{email}", dependencies=[Depends(require_permission("admin_emails.manage"))])
def remove_admin_email(email: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    try:
        emails = repo.remove_admin_email(email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    audit.log_action(db, current_user.username, "admin_email.remove", f"email:{email}")
    return {"emails": emails}
