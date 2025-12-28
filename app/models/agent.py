# app/models/agent.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    # Credentials
    api_id = Column(String, nullable=False)
    api_hash = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    session_string = Column(Text, nullable=False)
    user_id = Column(BigInteger, unique=True) # Telegram User ID of the agent itself
    
    # Status
    is_active = Column(Boolean, default=True) # Used for assignment logic
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    
    # Timing & Durations
    first_joined_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    total_active_seconds = Column(Float, default=0.0) # Cumulative duration
    
    # Stats (Cached for quick access, calculated from logs)
    daily_adds = Column(Integer, default=0)
    monthly_adds = Column(Integer, default=0)
    total_adds = Column(Integer, default=0)

    # Relationships
    sessions = relationship("AgentSession", back_populates="agent")
    source_memberships = relationship("AgentGroupMembership", back_populates="agent")
    # Note: operations relationship is in logs.py

class AgentSession(Base):
    """Tracks each time an agent comes online/offline to calculate total duration."""
    __tablename__ = 'agent_sessions'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True) # Null if currently active
    
    agent = relationship("Agent", back_populates="sessions")

class AgentGroupMembership(Base):
    """Tracks which Source Groups an Agent is currently inside."""
    __tablename__ = 'agent_group_memberships'
    
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    group_id = Column(BigInteger, ForeignKey('groups.id'), primary_key=True)
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="source_memberships")
    # Relationship to Group must be defined explicitly using string name
    group = relationship("Group", back_populates="agents_inside")