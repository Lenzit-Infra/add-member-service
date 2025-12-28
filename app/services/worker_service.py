# app/services/worker_service.py
import asyncio
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.database import SessionLocal
from app.repositories.order_repo import OrderRepository
from app.modules.scraper.service import ScraperService
from app.modules.adder.service import AdderService 
from app.models.order import Order, OrderStatus
from app.repositories.scraper_repo import ScraperRepository
from app.repositories.settings_repo import SettingsRepository # NEW IMPORT

class WorkerService:
    def __init__(self):
        self.db = SessionLocal() 
        self.order_repo = OrderRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)
        # Initialize defaults on startup
        self.settings_repo.initialize_defaults()
        
    async def process_batch_for_order(self, order: Order):
        # ... (Previous code remains the same until 'Add' step) ...
        # Fetch dynamic settings
        batch_size = int(self.settings_repo.get_setting("batch_size", "5"))
        sleep_min = int(self.settings_repo.get_setting("sleep_delay_min", "10"))
        sleep_max = int(self.settings_repo.get_setting("sleep_delay_max", "30"))

        print(f"WORKER: Processing Order {order.id} with Batch Size: {batch_size}")

        # 1. Select Agent and Initialize Client
        agent_record = self.order_repo.get_available_agent()
        if not agent_record:
            print("WORKER: No active agents available.")
            return

        client = TelegramClient(
            StringSession(agent_record.session_string),
            agent_record.api_id,
            agent_record.api_hash
        )
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"WORKER: Agent {agent_record.phone} session expired.")
                await client.disconnect()
                return

            # 2. Scrape Logic (Unchanged)
            if not order.source_groups:
                return
            source_link = order.source_groups[0].group.invite_link
            scraper_service = ScraperService(client)
            scraped_data = await scraper_service.scrape_group(source_link, min_score=40)
            
            repo = ScraperRepository(self.db)
            existing_ids = repo.get_existing_user_ids()
            new_users = [u for u in scraped_data if u['user_id'] not in existing_ids]
            repo.bulk_save_members(new_users)
            
            # 3. Add Logic (Dynamic Count)
            adder_service = AdderService(client, self.db)
            successful_adds = await adder_service.add_users_to_group(
                target_group_link=order.target_group.invite_link, 
                agent_id=agent_record.id,
                target_group_id=order.target_group.id,
                count=batch_size  # USING DYNAMIC SETTING
            )

            is_completed = self.order_repo.increment_order_count(order.id, successful_adds)
            
            # 4. Dynamic Sleep
            # Only sleep if we actually added someone to allow cool-down
            if successful_adds > 0:
                delay = random.randint(sleep_min, sleep_max)
                print(f"WORKER: Cooling down for {delay} seconds (Configured Range: {sleep_min}-{sleep_max})...")
                await asyncio.sleep(delay)
                 
        except Exception as e:
            print(f"WORKER ERROR: {e}")
        finally:
            if client.is_connected():
                await client.disconnect()

    async def run_periodic_check(self):
        try:
            # Check dynamic interval setting (Note: Changing this only affects logic inside the loop, not the scheduler trigger itself)
            # To make scheduler interval dynamic, we would need to restart scheduler. 
            # For now, we keep the check rapid, but we can implement logic to skip checks here if needed.
            
            order = self.order_repo.get_pending_or_in_progress_order()
            if order:
                print(f"SCHEDULER: Found active Order {order.id}.")
                await self.process_batch_for_order(order)
            else:
                pass # Silent when no order to reduce log noise
            
            self.db.commit()
        except Exception as e:
            print(f"SCHEDULER ERROR: {e}")
            self.db.rollback()