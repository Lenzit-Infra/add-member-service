# run_worker.py
import sys
import os
# backend/ root (parent of this scripts/ dir) must be on sys.path so "app.*" resolves
# regardless of the caller's working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging_config import setup_logging
setup_logging("worker")  # backend/logs/worker.log — must run before anything else logs/prints

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.worker_service import WorkerService
from app.services.movement_monitor_service import MovementMonitorService
from app.core.database import Base, engine, SessionLocal
from app.core.migrations import run_lightweight_migrations
from app.repositories.settings_repo import SettingsRepository
# Import all models to ensure tables are created
from app.models import agent, group, member, order, logs, user, settings, audit_log
import time

# Ensure all database tables are created + apply lightweight migrations
Base.metadata.create_all(bind=engine)
run_lightweight_migrations(engine)

# Read scheduler intervals once at startup (Settings → Worker & Throughput).
# Changing these in the dashboard requires restarting this process to take
# effect — APScheduler jobs are scheduled once below, not re-read per tick.
_settings_db = SessionLocal()
_settings_repo = SettingsRepository(_settings_db)
_settings_repo.initialize_defaults()
WORKER_CHECK_INTERVAL_SECONDS = int(_settings_repo.get_setting("worker_check_interval", "10"))
MOVEMENT_MONITOR_INTERVAL_MINUTES = int(_settings_repo.get_setting("movement_monitor_interval_minutes", "5"))
_settings_db.close()

async def start_scheduler():
    """Sets up the scheduler and runs the main loop asynchronously."""
    print("--- STARTING BACKGROUND WORKER & SCHEDULER ---")

    # Initialize the worker service
    worker = WorkerService()
    movement_monitor = MovementMonitorService()

    # 1. Setup APScheduler
    scheduler = AsyncIOScheduler()

    # 2. Add the job: Run the order-processing check
    scheduler.add_job(
        worker.run_periodic_check,
        'interval',
        seconds=WORKER_CHECK_INTERVAL_SECONDS,
        id='order_processor'
    )

    # 2b. Phase 4: Member Movement Monitor — runs less frequently by default
    # to avoid competing with the adder/scraper for agent flood limits.
    scheduler.add_job(
        movement_monitor.run_check,
        'interval',
        minutes=MOVEMENT_MONITOR_INTERVAL_MINUTES,
        id='movement_monitor'
    )

    # 3. Start the scheduler (now called within the asyncio context)
    scheduler.start()

    print("Scheduler initialized. Press Ctrl+C to exit.")
    print(f"Worker is now checking for active orders every {WORKER_CHECK_INTERVAL_SECONDS} seconds.")
    print(f"Member Movement Monitor is checking target groups every {MOVEMENT_MONITOR_INTERVAL_MINUTES} minutes.")
    
    # 4. Keep the asyncio loop running indefinitely
    try:
        # Use a simple loop to keep the process alive indefinitely
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("\nScheduler shut down gracefully.")
        

def main():
    """Synchronous entry point that starts the asyncio loop."""
    try:
        # asyncio.run() sets up the loop and runs the async function to completion
        asyncio.run(start_scheduler())
    except Exception as e:
        print(f"FATAL ERROR in main execution: {e}")

if __name__ == "__main__":
    main()