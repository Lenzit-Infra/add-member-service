# app/services/audit.py
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

MAX_PAGE_SIZE = 100


def log_action(db: Session, actor_username: str, action: str, target: str = None, details: str = None):
    db.add(AuditLog(actor_username=actor_username, action=action, target=target, details=details))
    db.commit()


def get_recent(db: Session, limit: int = 300):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def list_actions(db: Session) -> list:
    """Distinct action types seen so far — backs the filter dropdown."""
    rows = db.query(AuditLog.action).distinct().order_by(AuditLog.action.asc()).all()
    return [r[0] for r in rows]


def search(db: Session, actor: str = None, action: str = None, date_from=None, date_to=None, page: int = 1, page_size: int = 25):
    page = max(1, page)
    page_size = max(1, min(MAX_PAGE_SIZE, page_size))

    query = db.query(AuditLog)
    if actor:
        query = query.filter(AuditLog.actor_username.ilike(f"%{actor}%"))
    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AuditLog.timestamp <= date_to)

    total = query.count()
    items = (
        query.order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
