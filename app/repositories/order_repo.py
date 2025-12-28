# app/repositories/order_repo.py
from sqlalchemy.orm import Session
from typing import Optional # <--- IMPORT ADDED
from app.models.order import Order, OrderStatus
from app.models.agent import Agent
from datetime import datetime

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pending_or_in_progress_order(self) -> Optional[Order]: # <--- FIXED TYPE HINT
        """Fetch the highest priority order that needs processing."""
        # Worker should pick up IN_PROGRESS or PENDING_AGENT
        return self.db.query(Order)\
            .filter(Order.status.in_([OrderStatus.IN_PROGRESS, OrderStatus.PENDING_AGENT]))\
            .first()

    def update_order_status(self, order_id: int, status: OrderStatus):
        """Updates the status of an order."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            if status in [OrderStatus.FINISHED, OrderStatus.CANCELLED]:
                order.ended_at = datetime.utcnow()
            self.db.commit()

    def increment_order_count(self, order_id: int, count: int) -> bool:
        """Increments the current_count and checks for completion."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.current_count += count
            
            # Check if finished
            if order.current_count >= order.desired_count:
                order.status = OrderStatus.FINISHED
                order.ended_at = datetime.utcnow()
                print(f"Order {order_id} reached desired count and is marked FINISHED.")
                
            self.db.commit()
            return order.status == OrderStatus.FINISHED
        return False

    def get_available_agent(self) -> Optional[Agent]: # <--- FIXED TYPE HINT
        """Finds an agent that is active and not currently banned."""
        return self.db.query(Agent)\
            .filter(Agent.is_active == True, Agent.is_banned == False)\
            .first()