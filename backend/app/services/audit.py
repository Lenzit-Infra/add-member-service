# app/services/audit.py
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(db: Session, actor_username: str, action: str, target: str = None, details: str = None):
    db.add(AuditLog(actor_username=actor_username, action=action, target=target, details=details))
    db.commit()


def get_recent(db: Session, limit: int = 300):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
