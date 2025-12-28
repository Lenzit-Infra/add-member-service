import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Core Imports
from app.models.agent import Agent 
from app.core.database import SessionLocal, Base, engine 
# Ensure all models are loaded
from app.models import agent, group, member, order, logs 

# Controller Import
from app.modules.scraper.controller import start_scraping_process

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

async def main():
    # 1. Select an Account from DB
    db = SessionLocal()
    # Replace with your active phone number
    phone_number = "+989374741941" 
    agent_record = db.query(Agent).filter(Agent.phone == phone_number).first()
    db.close()

    if not agent_record:
        print(f"Error: Agent {phone_number} not found. Run add_account.py first.")
        return

    print(f"Using Agent: {agent_record.phone}")

    # 2. Initialize Client
    client = TelegramClient(
        StringSession(agent_record.session_string),
        agent_record.api_id,
        agent_record.api_hash
    )

    await client.connect()

    if not await client.is_user_authorized():
        print("Error: Agent session expired. Run add_account.py to relogin.")
        return

    # 3. Start the Scraper Controller
    await start_scraping_process(client)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())