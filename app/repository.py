from sqlalchemy.orm import Session
from app.modules.scraper.models import ScrapedMember

class ScraperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_existing_user_ids(self):
        """
        Fetches all user_ids currently in the database to prevent duplicates.
        Returns a Set for O(1) lookup speed.
        """
        result = self.db.query(ScrapedMember.user_id).all()
        return {row[0] for row in result}

    def bulk_save_members(self, members_data: list):
        """
        Saves a list of dictionaries to the database in a single batch transaction.
        This is much faster than saving one by one.
        """
        if not members_data:
            return 0

        # Convert dictionary data to Model instances
        db_objects = [ScrapedMember(**data) for data in members_data]
        
        try:
            self.db.bulk_save_objects(db_objects)
            self.db.commit()
            return len(db_objects)
        except Exception as e:
            self.db.rollback()
            print(f"Database Error: {e}")
            return 0