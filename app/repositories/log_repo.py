# app/repositories/log_repo.py
from sqlalchemy.orm import Session
from app.models.logs import OperationLog, OperationStatus

class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_operation(self, 
                      user_id: int, 
                      agent_id: int, 
                      target_group_id: int,
                      status: OperationStatus, 
                      error_message: str = None):
        """
        Records the result of an operation (e.g., inviting a user) into the OperationLog table.
        """
        log_entry = OperationLog(
            member_id=user_id,  # <--- FIX: Changed from user_id to member_id
            agent_id=agent_id,
            target_group_id=target_group_id,
            status=status,
            fail_reason=error_message # <--- Note: Model uses fail_reason, ensuring consistency
        )
        self.db.add(log_entry)
        # We don't commit here; the caller (WorkerService) handles the final commit.
        return log_entry