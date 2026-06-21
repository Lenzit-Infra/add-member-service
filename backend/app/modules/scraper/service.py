# app/modules/scraper/service.py
import asyncio
from telethon import TelegramClient
from telethon.tl.types import UserStatusOnline, UserStatusRecently, UserStatusOffline, UserStatusEmpty
# CORRECT IMPORT:
from app.models.member import Member

class ScraperService:
    def __init__(self, client: TelegramClient):
        self.client = client

    def _calculate_user_score(self, user):
        """
        Calculates a quality score (0-100) for a user based on their profile.
        This uses the updated scoring logic based on profile completeness and activity.
        """
        score = 0

        # High priority checks
        if user.premium: 
            score += 100
            return score
        
        # Check for profile photo
        if user.photo:
            score += 30

        # Check for username
        if user.username:
            score += 20

        # Check online status (Most important factor for activity)
        if isinstance(user.status, UserStatusOnline):
            score += 50
        elif isinstance(user.status, UserStatusRecently):
            score += 30
        elif isinstance(user.status, UserStatusOffline):
            # Give a small score if they were offline recently (not long_ago)
            score += 10
        
        # Filter 3: Check for suspicious flags
        if user.scam or user.fake:
            score -= 50

        return score

    async def scrape_group(self, group_link: str, min_score=40):
        """
        Connects to the group, extracts members, and filters them based on quality score.
        Returns a list of dictionaries containing user data ready for the repository.
        """
        print(f"Resolving entity: {group_link}...")
        try:
            entity = await self.client.get_entity(group_link)
        except ValueError:
            print("Error: Could not find the group. Check the link.")
            return []
        except Exception as e:
            print(f"Error resolving group: {e}")
            return []

        print(f"Group found: {entity.title}. Starting extraction...")
        
        try:
            # aggressive=True is essential for large groups
            participants = await self.client.get_participants(entity, aggressive=True)
        except Exception as e:
            print(f"Error fetching participants: {e}")
            return []

        print(f"Total raw participants found: {len(participants)}")

        cleaned_data = []
        rejected_count = 0

        for user in participants:
            # Filter 1: Absolute Rejection (Bots, Deleted, Empty Status)
            if user.bot or user.deleted or isinstance(user.status, UserStatusEmpty):
                rejected_count += 1
                continue

            # Filter 2: Quality Scoring
            quality_score = self._calculate_user_score(user)

            if quality_score < min_score:
                rejected_count += 1
                continue

            # Determine User Status string for database
            # CRITICAL FIX: Ensure all status strings are UPPERCASE to match the Enum definition
            status_str = "UNKNOWN"
            if isinstance(user.status, UserStatusOnline):
                status_str = "ONLINE" 
            elif isinstance(user.status, UserStatusRecently):
                status_str = "RECENTLY" 
            elif isinstance(user.status, UserStatusOffline):
                status_str = "OFFLINE" 

            user_data = {
                "user_id": user.id,
                "access_hash": user.access_hash,
                "username": user.username,
                "first_name": user.first_name,
                "status": status_str, # Storing standardized uppercase string
                "quality_score": quality_score, 
                "is_premium": user.premium, 
                "is_scam": user.scam, 
                "is_fake": user.fake 
            }
            cleaned_data.append(user_data)

        print(f"Quality Filter Report: Kept {len(cleaned_data)} | Rejected {rejected_count} (Low Score/Invalid)")
        return cleaned_data