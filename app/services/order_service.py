# app/services/order_service.py
from sqlalchemy.orm import Session
from telethon import TelegramClient, functions
from telethon.tl.types import ChannelParticipantAdmin, Channel, Chat
from app.models.order import Order, OrderStatus
from app.models.group import Group
from app.repositories.group_repo import GroupRepository
import random

LENZIT_BOT_USERNAME = "@Lenzit_bot" 

class OrderService:
    def __init__(self, db: Session, client: TelegramClient):
        self.db = db
        self.client = client
        self.group_repo = GroupRepository(db)

    # ... (Method _validate_lenzit_admin remains unchanged) ...
    async def _validate_lenzit_admin(self, target_entity) -> bool:
        # (Copy your previous validation logic here or keep the file content if unchanged except create_new_order)
        # For brevity, I assume you have the validation logic.
        return True 

    async def create_new_order(self, target_link: str, source_links: list, desired_count: int) -> Order or None:
        try:
            # ... (Validation Logic) ...
            target_entity = await self.client.get_entity(target_link)
            target_group = self.group_repo.find_or_create_group(target_entity, group_type='target', invite_link=target_link)
            
            # Generate 6-digit ID
            while True:
                new_id = random.randint(100000, 999999)
                if not self.db.query(Order).filter(Order.id == new_id).first():
                    break

            new_order = Order(
                id=new_id,
                target_group_id=target_group.id,
                desired_count=desired_count,
                # FIX: Set initial status to PENDING_AGENT
                status=OrderStatus.PENDING_AGENT 
            )
            self.db.add(new_order)
            self.db.flush() 

            # ... (Source Group Linking Logic) ...
            # (Keep your existing logic for linking source groups)
            
            self.db.commit()
            return new_order

        except Exception as e:
            self.db.rollback()
            print(f"Error: {e}")
            return None