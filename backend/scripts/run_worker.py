# run_worker.py
import sys
import os
# backend/ root (parent of this scripts/ dir) must be on sys.path so "app.*" resolves
# regardless of the caller's working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.worker_service import WorkerService
from app.services.movement_monitor_service import MovementMonitorService
from app.core.database import Base, engine
from app.core.migrations import run_lightweight_migrations
# Import all models to ensure tables are created
from app.models import agent, group, member, order, logs, user
import time

# Ensure all database tables are created + apply lightweight migrations
Base.metadata.create_all(bind=engine)
run_lightweight_migrations(engine)

async def start_scheduler():
    """Sets up the scheduler and runs the main loop asynchronously."""
    print("--- STARTING BACKGROUND WORKER & SCHEDULER ---")

    # Initialize the worker service
    worker = WorkerService()
    movement_monitor = MovementMonitorService()

    # 1. Setup APScheduler
    scheduler = AsyncIOScheduler()

    # 2. Add the job: Run the check every 10 seconds
    # FIX: Changed interval from minutes=1 to seconds=10
    scheduler.add_job(
        worker.run_periodic_check,
        'interval',
        seconds=10,
        id='order_processor'
    )

    # 2b. Phase 4: Member Movement Monitor — runs less frequently (every 5 minutes)
    # to avoid competing with the adder/scraper for agent flood limits.
    scheduler.add_job(
        movement_monitor.run_check,
        'interval',
        minutes=5,
        id='movement_monitor'
    )

    # 3. Start the scheduler (now called within the asyncio context)
    scheduler.start()

    print("Scheduler initialized. Press Ctrl+C to exit.")
    # FIX: Updated message to reflect the new 10-second interval
    print("Worker is now checking for active orders every 10 seconds.")
    print("Member Movement Monitor is checking target groups every 5 minutes.")
    
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