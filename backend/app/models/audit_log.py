# app/models/audit_log.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.database import Base


class AuditLog(Base):
    """Trail of every admin/operator mutating action — who did what, when.
    actor_username is denormalized (not a FK) so the row still makes sense
    even if the acting user is later deleted."""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    actor_username = Column(String, nullable=False)
    action = Column(String, nullable=False)  # e.g. "user.create", "settings.update"
    target = Column(String, nullable=True)   # e.g. "user:mehran"
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
