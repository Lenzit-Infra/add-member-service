from app.modules.adder.service import AdderService
from app.core.database import SessionLocal
from telethon import TelegramClient

async def start_adding_process(client: TelegramClient):
    """
    Controller to handle user input and start the adder service.
    """
    # 1. Input Target Group
    target_link = input("Enter the TARGET Group Link (Where users will be added): ").strip()
    
    # 2. Input Count
    try:
        count_input = input("How many users to add in this batch? (Recommended: 10-20): ").strip()
        count = int(count_input)
    except ValueError:
        print("Invalid number. Defaulting to 5.")
        count = 5

    # 3. Start Service
    db = SessionLocal()
    service = AdderService(client, db)
    
    await service.add_users_to_group(target_link, count)
    
    db.close()