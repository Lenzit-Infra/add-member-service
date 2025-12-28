# app/models/settings.py
from sqlalchemy import Column, String, Integer
from app.core.database import Base

class SystemSetting(Base):
    """
    Stores key-value configurations for the system.
    """
    __tablename__ = 'system_settings'

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False) # We store everything as string and cast later
    description = Column(String, nullable=True)