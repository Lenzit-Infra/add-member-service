# app/services/movement_monitor_service.py
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.database import SessionLocal
from app.repositories.order_repo import OrderRepository
from app.models.group import Group
from app.models.order import Order
from app.models.member import Member
from app.models.logs import MemberMovement
from app.core.telegram_proxy import get_proxy


class MovementMonitorService:
    """
    Phase 4: Tracks members leaving Target Groups.
    For each group that has been used as an Order target, diffs the live
    Telegram participant list against the members we know we've added,
    and records joins/leaves into MemberMovement.
    """

    def __init__(self):
        self.db = SessionLocal()
        self.order_repo = OrderRepository(self.db)

    async def run_check(self):
        try:
            target_groups = (
                self.db.query(Group)
                .join(Order, Order.target_group_id == Group.id)
                .distinct()
                .all()
            )
            if not target_groups:
                return

            agent_record = self.order_repo.get_available_agent()
            if not agent_record:
                print("MOVEMENT MONITOR: No active agent available.")
                return

            client = TelegramClient(
                StringSession(agent_record.session_string),
                agent_record.api_id,
                agent_record.api_hash,
                proxy=get_proxy(),
            )

            try:
                await client.connect()
                if not await client.is_user_authorized():
                    print(f"MOVEMENT MONITOR: Agent {agent_record.phone} session expired.")
                    return

                for group in target_groups:
                    await self._check_group(client, group)

            finally:
                if client.is_connected():
                    await client.disconnect()

        except Exception as e:
            print(f"MOVEMENT MONITOR ERROR: {e}")
            self.db.rollback()

    async def _check_group(self, client: TelegramClient, group: Group):
        if not group.username and not group.invite_link:
            return

        try:
            entity = await client.get_entity(group.username or group.invite_link)
            participants = await client.get_participants(entity, aggressive=True)
        except Exception as e:
            print(f"MOVEMENT MONITOR: Could not fetch participants for {group.title}: {e}")
            return

        current_ids = {p.id for p in participants}

        # Only track members we recruited ourselves (present in our Member table)
        our_member_ids = {m.user_id for m in self.db.query(Member.user_id).all()}

        active_movements = (
            self.db.query(MemberMovement)
            .filter(MemberMovement.group_id == group.id, MemberMovement.left_at.is_(None))
            .all()
        )
        known_active_ids = {m.member_id for m in active_movements}

        left_ids = (known_active_ids & our_member_ids) - current_ids
        joined_ids = (current_ids & our_member_ids) - known_active_ids

        for movement in active_movements:
            if movement.member_id in left_ids:
                movement.left_at = datetime.utcnow()

        for member_id in joined_ids:
            self.db.add(MemberMovement(member_id=member_id, group_id=group.id, joined_at=datetime.utcnow()))

        if left_ids or joined_ids:
            print(f"MOVEMENT MONITOR: {group.title} — {len(joined_ids)} joined, {len(left_ids)} left")

        self.db.commit()
