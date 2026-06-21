from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.settings_repo import SettingsRepository
from .schemas import SettingUpdate

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
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    keys = ["batch_size", "sleep_delay_min", "sleep_delay_max", "daily_limit_per_agent", "worker_check_interval"]
    return {k: repo.get_setting(k) for k in keys}

@router.post("/settings")
def update_setting(data: SettingUpdate, db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.set_setting(data.key, data.value)
    return {"status": "success", "key": data.key, "value": data.value}
