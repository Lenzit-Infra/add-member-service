import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.models import Account, SessionLocal
from app.core.database import Base, engine
from app.modules.adder.controller import start_adding_process

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

async def main():
    # 1. Login Logic
    db = SessionLocal()
    # Change phone number if needed
    phone_number = "+989374741941"
    account = db.query(Account).filter_by(phone=phone_number).first()
    db.close()

    if not account:
        print("Error: Account not found. Run add_account.py first.")
        return

    print(f"Using Account: {account.phone}")

    # 2. Connect Telegram
    client = TelegramClient(
        StringSession(account.session_string),
        account.api_id,
        account.api_hash
    )

    await client.connect()

    if not await client.is_user_authorized():
        print("Error: Session expired.")
        return

    # 3. Run Adder Controller
    await start_adding_process(client)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())