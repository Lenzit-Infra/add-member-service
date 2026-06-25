# app/services/worker_service.py
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.database import SessionLocal
from app.repositories.order_repo import OrderRepository
from app.modules.scraper.service import ScraperService
from app.modules.adder.service import AdderService
from app.models.order import Order, OrderStatus
from app.repositories.scraper_repo import ScraperRepository
from app.repositories.settings_repo import SettingsRepository
from app.services import agent_selector
from app.services import health
from app.core.telegram_proxy import get_proxy

logger = logging.getLogger("worker")

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
        daily_limit = int(self.settings_repo.get_setting("daily_limit_per_agent", "30"))
        new_agent_limit = int(self.settings_repo.get_setting("new_agent_daily_limit", "5"))
        warmup_days = int(self.settings_repo.get_setting("new_agent_warmup_days", "14"))
        auto_pause_ratio = float(self.settings_repo.get_setting("auto_pause_failure_ratio", "0.9"))

        print(f"WORKER: Processing Order {order.id} with Batch Size: {batch_size}")

        # 1. Select Agent and Initialize Client (anti-ban-aware: load-balanced,
        # skips agents at today's capacity or in flood-wait cooldown, and caps
        # newer agents at a lower daily limit during their warm-up period)
        agent_record = self.order_repo.get_available_agent(daily_limit, new_agent_limit, warmup_days)
        if not agent_record:
            print("WORKER: No eligible agents available (all busy, at capacity, in cooldown, or banned).")
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
            adder_result = await adder_service.add_users_to_group(
                target_group_link=order.target_group.invite_link,
                agent_id=agent_record.id,
                target_group_id=order.target_group.id,
                count=batch_size,  # USING DYNAMIC SETTING
                sleep_min=sleep_min,
                sleep_max=sleep_max,
            )
            successful_adds = adder_result["success_count"]

            # Telegram told us to back off — put this agent in cooldown so the
            # selector skips it until the wait expires, instead of hammering it again.
            if adder_result["flood_wait_seconds"]:
                agent_record.cooldown_until = datetime.utcnow() + timedelta(seconds=adder_result["flood_wait_seconds"])
                self.db.commit()
                print(f"WORKER: Agent {agent_record.phone} entering cooldown until {agent_record.cooldown_until} (FloodWait {adder_result['flood_wait_seconds']}s)")

            is_completed = self.order_repo.increment_order_count(order.id, successful_adds)

            # 4. Circuit breaker: if this agent's recent attempts are mostly
            # failing, auto-pause it (is_active=False) instead of letting the
            # worker keep hammering a likely-restricted account. A human has
            # to look at it and re-activate it from the Agents page.
            failure_ratio = agent_selector.get_recent_failure_ratio(self.db, agent_record.id)
            if failure_ratio >= auto_pause_ratio and agent_record.is_active:
                agent_record.is_active = False
                agent_record.pause_reason = f"Auto-paused: {failure_ratio:.0%} of recent attempts failed"
                self.db.commit()
                print(f"WORKER: Auto-paused agent {agent_record.phone} — {agent_record.pause_reason}")

        except Exception:
            logger.exception(f"WORKER ERROR processing order {order.id} with agent {agent_record.phone}")
        finally:
            if client.is_connected():
                await client.disconnect()

    async def run_periodic_check(self):
        try:
            # Heartbeat for the dashboard's backend-status indicator — written every
            # tick regardless of whether there's an active order, so "worker is alive"
            # and "worker is processing something" stay independently observable.
            health.record_worker_heartbeat(self.db)
            if health.should_recheck_telegram(self.db):
                # Blocking socket call — run off the event loop so a stalled/blocked
                # network doesn't freeze this 10s-interval scheduler job.
                reachable = await asyncio.to_thread(health.probe_telegram_reachable)
                health.record_telegram_reachability(self.db, reachable)

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
        except Exception:
            logger.exception("SCHEDULER ERROR in run_periodic_check")
            self.db.rollback()