from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent
from app.repositories.analytics_repo import AnalyticsRepository

router = APIRouter()

def _get_agent_or_404(agent_id: int, db: Session) -> Agent:
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.patch("/{agent_id}/toggle-active")
def toggle_active(agent_id: int, db: Session = Depends(get_db)):
    agent = _get_agent_or_404(agent_id, db)
    agent.is_active = not agent.is_active
    if agent.is_active:
        agent.pause_reason = None  # manual re-activation clears any auto-pause note
    db.commit()
    return {"status": "success", "id": agent.id, "is_active": agent.is_active}

@router.patch("/{agent_id}/toggle-ban")
def toggle_ban(agent_id: int, db: Session = Depends(get_db)):
    agent = _get_agent_or_404(agent_id, db)
    agent.is_banned = not agent.is_banned
    agent.ban_reason = "Manually banned via dashboard" if agent.is_banned else None
    db.commit()
    return {"status": "success", "id": agent.id, "is_banned": agent.is_banned}

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = _get_agent_or_404(agent_id, db)
    db.delete(agent)
    db.commit()
    return {"status": "success", "id": agent_id}

@router.get("/{agent_id}/history")
def get_agent_history(agent_id: int, db: Session = Depends(get_db)):
    _get_agent_or_404(agent_id, db)
    return AnalyticsRepository(db).get_agent_history(agent_id)
