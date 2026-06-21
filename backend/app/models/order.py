# app/models/order.py
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.common import OrderStatus 

class Order(Base):
    __tablename__ = 'orders'

    # Using explicit ID generation (not autoincrement) based on your request for 6-digit IDs
    id = Column(Integer, primary_key=True, autoincrement=False)
    
    target_group_id = Column(BigInteger, ForeignKey('groups.id'))
    
    desired_count = Column(Integer, nullable=False)
    current_count = Column(Integer, default=0) 
    
    # FIX: Changed default from PENDING to PENDING_AGENT
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_AGENT)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True) # Added ended_at field
    
    # Relationships
    target_group = relationship("Group", back_populates="orders_as_target", foreign_keys=[target_group_id])
    source_groups = relationship("OrderSourceGroup", back_populates="order")

class OrderSourceGroup(Base):
    """Many-to-Many: Which source groups are used for a specific order."""
    __tablename__ = 'order_source_groups'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    source_group_id = Column(BigInteger, ForeignKey('groups.id'))
    
    # Relationships
    order = relationship("Order", back_populates="source_groups")
    group = relationship("Group", foreign_keys=[source_group_id])