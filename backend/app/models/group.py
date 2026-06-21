# app/models/group.py
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Group(Base):
    __tablename__ = 'groups'

    id = Column(BigInteger, primary_key=True) 
    type = Column(String) 
    title = Column(String)
    username = Column(String, nullable=True) 
    invite_link = Column(String, nullable=True) 

    is_lenzit_admin = Column(Boolean, default=False) 
    member_count = Column(Integer, default=0) 
    admin_count = Column(Integer, default=0)
    stats_history = Column(JSON, default=list)

    # Relationships
    agents_inside = relationship("AgentGroupMembership", back_populates="group")
    
    # and must be explicitly defined to avoid grabbing the source_group_id foreign key.
    member_movements = relationship(
        "MemberMovement", 
        back_populates="group", 
        foreign_keys="[MemberMovement.group_id]" # Explicitly target the primary link
    )
    
    orders_as_target = relationship("Order", back_populates="target_group")