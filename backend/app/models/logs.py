# app/models/logs.py
from sqlalchemy import Column, Integer, BigInteger, Enum, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.common import OperationStatus

class OperationLog(Base):
    """
    Records every single attempt to add a member.
    """
    __tablename__ = 'operations_logs'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    agent_id = Column(Integer, ForeignKey('agents.id'))
    member_id = Column(BigInteger, ForeignKey('members.user_id'))
    
    # FKeys link to groups table, creating ambiguity
    source_group_id = Column(BigInteger, ForeignKey('groups.id'))
    target_group_id = Column(BigInteger, ForeignKey('groups.id'))
    
    status = Column(Enum(OperationStatus))
    fail_reason = Column(String, nullable=True) 
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Ambiguity Fix: Explicitly define foreign keys for all relationships pointing to the same table (Group)
    agent = relationship("Agent", foreign_keys=[agent_id])
    member = relationship("Member", foreign_keys=[member_id])
    order = relationship("Order", foreign_keys=[order_id])
    
    source_group = relationship("Group", foreign_keys=[source_group_id])
    target_group = relationship("Group", foreign_keys=[target_group_id])


class MemberMovement(Base):
    """
    Tracks retention (Join/Leave history).
    """
    __tablename__ = 'member_movements'

    id = Column(Integer, primary_key=True)
    member_id = Column(BigInteger, ForeignKey('members.user_id'))
    
    # Two foreign keys point to Group: group_id (Target) and source_group_id (Source)
    group_id = Column(BigInteger, ForeignKey('groups.id')) 
    source_group_id = Column(BigInteger, ForeignKey('groups.id'), nullable=True) 
    
    added_by_agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True) 
    
    member = relationship("Member", foreign_keys=[member_id])
    agent = relationship("Agent", foreign_keys=[added_by_agent_id])
    
    group = relationship("Group", foreign_keys=[group_id], back_populates="member_movements")
    
    source_group = relationship("Group", foreign_keys=[source_group_id])