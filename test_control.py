import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.models import SessionLocal, Account

# Main function to handle connection and testing
async def main():
    # 1. Database Connection
    db = SessionLocal()
    # Ensure you are querying the correct phone number used in the database
    account = db.query(Account).filter_by(phone='+989374741941').first()
    db.close()

    if not account:
        print("Error: Account not found in database.")
        return

    print(f"Account found: {account.phone}")
    print("Connecting to Telegram...")

    # 2. Initialize Telegram Client with stored Session String
    client = TelegramClient(
        StringSession(account.session_string),
        account.api_id,
        account.api_hash
    )

    await client.connect()

    # 3. Authorization Check
    if not await client.is_user_authorized():
        print("Error: Session is expired. Please login again.")
        return

    # Get current user information
    me = await client.get_me()
    
    print("Connection successful.")
    print(f"User ID: {me.id}")
    print(f"Name: {me.first_name}")

    # 4. CRITICAL CHECK: Verify if the account is a Bot or a Human
    if me.bot:
        print("---------------------------------------------------")
        print("CRITICAL WARNING: This account is detected as a BOT.")
        print("This project requires a HUMAN account (Userbot).")
        print("Bots cannot scrape members or add users to groups.")
        print("Please restart the process with a real phone number.")
        print("---------------------------------------------------")
    else:
        # Only send message if it is a real user
        try:
            # 'me' refers to Saved Messages, which only works for humans
            await client.send_message('me', 'System check: Connection is stable.')
            print("Test message sent to Saved Messages.")
        except Exception as e:
            print(f"Failed to send message: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())