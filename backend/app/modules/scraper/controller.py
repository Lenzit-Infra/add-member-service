from telethon import TelegramClient
from app.core.database import SessionLocal
# UPDATED IMPORTS:
from app.modules.scraper.service import ScraperService
from app.repositories.scraper_repo import ScraperRepository 

async def start_scraping_process(client: TelegramClient):
    """
    The main entry point for the scraping module.
    """
    # 1. Input
    target_link = input("Enter the Source Group Link: ").strip()
    
    # 2. Service Layer (Logic)
    service = ScraperService(client)
    
    # We set a minimum quality score threshold of 40
    scraped_data = await service.scrape_group(target_link, min_score=40)
    
    if not scraped_data:
        print("No valid members found after filtering.")
        return

    # 3. Repository Layer (Database)
    db = SessionLocal()
    # Using the new centralized repository
    repo = ScraperRepository(db)
    
    # Deduplication: Remove users that are already in DB
    print("Checking for duplicates in database...")
    existing_ids = repo.get_existing_user_ids()
    new_users = [u for u in scraped_data if u['user_id'] not in existing_ids]

    duplicate_count = len(scraped_data) - len(new_users)
    print(f"Final Batch: {len(new_users)} new users ready to save (Duplicates removed: {duplicate_count})")

    if new_users:
        saved_count = repo.bulk_save_members(new_users)
        print(f"Success: Saved {saved_count} high-quality users to database.")
    
    db.close()