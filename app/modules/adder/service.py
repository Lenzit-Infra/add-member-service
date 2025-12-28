# app/modules/adder/service.py (UPDATED for Operation Logging)
import asyncio
import random
from telethon import TelegramClient, functions, errors
from telethon.tl.types import Chat, Channel
from sqlalchemy.orm import Session
from sqlalchemy import or_ 
from app.models.member import Member 
from app.repositories.log_repo import LogRepository # NEW: Import LogRepo
from app.models.logs import OperationStatus # NEW: Import OperationStatus Enum

class AdderService:
    def __init__(self, client: TelegramClient, db: Session):
        self.client = client
        self.db = db

    async def add_users_to_group(self, 
                                 target_group_link: str, 
                                 agent_id: int,             # NEW ARGUMENT
                                 target_group_id: int,      # NEW ARGUMENT
                                 count=10) -> int:
        """
        Main logic to add users from database to the target group.
        Returns the number of successfully added users (int).
        """
        # Initialize Log Repository
        log_repo = LogRepository(self.db) 
        
        print(f"Resolving target group: {target_group_link}...")
        try:
            target_entity = await self.client.get_entity(target_group_link)
        except Exception as e:
            print(f"Error resolving target group: {e}")
            return 0 

        # Fetch users... (Query remains unchanged)
        # ... (users_to_add query logic) ...
        users_to_add = self.db.query(Member)\
            .filter(
                or_(Member.has_privacy_restriction == False, Member.has_privacy_restriction == None),
            )\
            .order_by(Member.quality_score.desc())\
            .limit(count)\
            .all()
        # ... (end of query logic) ...

        if not users_to_add:
            print("No new users found in database to add.")
            return 0 

        print(f"Starting to add {len(users_to_add)} users to {target_entity.title}...")
        
        success_count = 0
        
        for user in users_to_add:
            status = OperationStatus.FAILED # Default status
            error_msg = None
            
            try:
                user_to_invite = await self.client.get_input_entity(user.user_id)

                await self.client(functions.channels.InviteToChannelRequest(
                    channel=target_entity, 
                    users=[user_to_invite]
                ))
                
                print("Success.")
                success_count += 1
                user.has_privacy_restriction = False 
                
                status = OperationStatus.SUCCESS # SUCCESS
                # Commit is postponed until log is created, for atomicity
                
                # ANTI-BAN PROTECTION: Random sleep 
                delay = random.randint(10, 30)
                print(f"Sleeping for {delay} seconds...")
                await asyncio.sleep(delay)

            except errors.FloodWaitError as e:
                print(f"CRITICAL: FloodWait triggered. Must wait {e.seconds} seconds.")
                status = OperationStatus.FAILED_FLOOD # Log Flood
                error_msg = str(e)
                break # Break on critical flood
            
            except errors.UserPrivacyRestrictedError:
                print("Failed: User's privacy settings prevent adding.")
                user.has_privacy_restriction = True 
                
                status = OperationStatus.FAILED_PRIVACY # Log Privacy
                error_msg = "User privacy settings restricted."
            
            except Exception as e:
                print(f"Error adding user: {e}")
                status = OperationStatus.FAILED_OTHER # Log Other Error
                error_msg = str(e)
                
            # --- NEW STEP: Log the operation result ---
            log_repo.log_operation(
                user_id=user.user_id,
                agent_id=agent_id,
                target_group_id=target_group_id,
                status=status,
                error_message=error_msg
            )
            # Commit the DB changes (Member status update and Log entry)
            self.db.commit()

        print(f"Operation finished. Successfully added {success_count} users.")
        return success_count