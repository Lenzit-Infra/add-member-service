# add_account.py
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

# NEW IMPORTS based on modular structure
from app.models.agent import Agent # Import the new Agent model
from app.core.database import Base, engine, SessionLocal # Import core DB functions
# Ensure all models are loaded for table creation
from app.models import agent, group, member, order, logs 


# Ensure all database tables are created before running
Base.metadata.create_all(bind=engine)

async def add_new_account():
    """
    Handles the explicit login process for a new Agent account and saves credentials.
    """
    print("--- Starting Explicit Agent Login Flow ---")
    
    # 1. Collect Credentials
    api_id = input("Enter API ID: ").strip()
    api_hash = input("Enter API Hash: ").strip()
    phone = input("Enter Phone Number (e.g., +989...): ").strip().replace(" ", "")

    print(f"\nConnecting to Telegram servers...")

    client = TelegramClient(StringSession(), api_id, api_hash)
    
    await client.connect()

    # 2. Authorization Process
    if not await client.is_user_authorized():
        try:
            # Step A: Request the login code
            print(f"Sending login code to {phone}...")
            await client.send_code_request(phone)
        except errors.FloodWaitError as e:
            print(f"Error: Flood Wait. You must wait {e.seconds} seconds.")
            return
        except Exception as e:
            print(f"Error sending code: {e}")
            return

        # Step B: Input the code and sign in
        try:
            code = input("Enter the 5-digit login code: ")
            await client.sign_in(phone, code)
        except errors.SessionPasswordNeededError:
            # Handle Two-Step Verification (2FA)
            print("Two-Step Verification is enabled.")
            password = input("Please enter your password: ")
            await client.sign_in(password=password)
        except errors.PhoneCodeInvalidError:
            print("Error: The code you entered is invalid.")
            return
        except Exception as e:
            print(f"Login failed: {e}")
            return

    # 3. Verification and Storage
    me = await client.get_me()
    
    print("\n--- Account Status ---")
    print(f"Name: {me.first_name}")
    print(f"ID: {me.id}")
    print(f"Is Bot: {me.bot}")

    if me.bot:
        print("CRITICAL ERROR: Account identified as a BOT. Operation aborted.")
        return

    # 4. Save Session to Database
    session_str = client.session.save()
    db = SessionLocal()
    
    try:
        # Check if agent exists (using the new Agent model)
        existing_agent = db.query(Agent).filter(Agent.phone == phone).first()
        
        if existing_agent:
            existing_agent.session_string = session_str
            existing_agent.api_id = api_id
            existing_agent.api_hash = api_hash
            existing_agent.user_id = me.id
            existing_agent.is_active = True
            print("Success: Agent account updated in database.")
        else:
            new_agent = Agent(
                phone=phone,
                api_id=api_id,
                api_hash=api_hash,
                session_string=session_str,
                user_id=me.id
            )
            db.add(new_agent)
            print("Success: New Agent account saved to database.")
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database Error: {e}")
    finally:
        db.close()
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_new_account())