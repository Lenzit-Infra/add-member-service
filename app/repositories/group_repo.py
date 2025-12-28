# app/repositories/group_repo.py
from sqlalchemy.orm import Session
from app.models.group import Group
from app.models.order import OrderSourceGroup
from telethon.tl.types import Channel, Chat

class GroupRepository:
    """
    Handles CRUD operations for Group entities.
    """
    def __init__(self, db: Session):
        self.db = db
        
    def find_or_create_group(self, group_entity, group_type: str, invite_link: str = None) -> Group:
        """
        Finds a group by its ID or creates a new record if it doesn't exist.
        """
        telegram_id = group_entity.id
        
        # Supergroups (Channel) IDs need a specific prefix in Telegram API
        if isinstance(group_entity, Channel):
             telegram_id = -100 * telegram_id
        elif isinstance(group_entity, Chat):
             # Basic Group IDs are generally negative, so we use the raw ID
             pass

        group = self.db.query(Group).filter(Group.id == telegram_id).first()

        if not group:
            group = Group(
                id=telegram_id,
                type=group_type,
                title=getattr(group_entity, 'title', 'N/A'),
                username=getattr(group_entity, 'username', None),
                invite_link=invite_link
            )
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
        
        return group

    def link_source_to_order(self, order_id: int, source_group_id: int):
        """
        Creates the Many-to-Many link between an Order and a Source Group.
        """
        link = OrderSourceGroup(
            order_id=order_id,
            source_group_id=source_group_id
        )
        self.db.add(link)
        self.db.commit()