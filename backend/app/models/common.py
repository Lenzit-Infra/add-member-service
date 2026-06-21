import enum

class OrderStatus(enum.Enum):
    """Status of an automation order."""
    PENDING_AGENT = "pending_agent" # Waiting for an available agent
    PAUSED = "paused"               # Temporarily halted
    IN_PROGRESS = "in_progress"     # Running
    CANCELLED = "cancelled"         # Stopped permanently
    FINISHED = "finished"           # Completed successfully

class OperationStatus(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    FAILED_FLOOD = "failed_flood"
    FAILED_PRIVACY = "failed_privacy"
    FAILED_OTHER = "failed_other"

class MemberStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    RECENTLY = "recently"
    WITHIN_WEEK = "within_week"
    WITHIN_MONTH = "within_month"
    LONG_AGO = "long_ago"
    UNKNOWN = "unknown"