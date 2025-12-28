# run_order.py
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.models.agent import Agent
from app.core.database import SessionLocal, Base, engine 
# Import all models to ensure tables are created during startup
from app.models import agent, group, member, order, logs 
from app.controllers.order_controller import create_order_cli

# Ensure all database tables are created before running
Base.metadata.create_all(bind=engine)

async def main():
    """
    Main runner for the Order Creation process.
    Loads the Agent and calls the CLI controller.
    """
    # 1. Select an Account (Agent) for API interactions
    db = SessionLocal()
    # Replace with the phone number of the active agent you want to use
    phone_number = "+989374741941" 
    agent_record = db.query(Agent).filter(Agent.phone == phone_number).first()
    db.close()

    if not agent_record:
        print(f"Error: Agent {phone_number} not found. Run add_account.py first.")
        return

    print(f"System initialized. Using Agent: {agent_record.phone}")

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

    # 3. Start the Order Creation Controller
    await create_order_cli(client)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())