# app/controllers/dashboard_controller.py
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.analytics_repo import AnalyticsRepository

router = APIRouter(prefix="/api/v1")

# Initialize FastAPI app
app = FastAPI(
    title="Telegram Automation Dashboard API",
    description="API for tracking Agent performance and Order progress."
)

@router.get("/agents/summary")
def get_agents_summary(db: Session = Depends(get_db)):
    """
    Retrieves performance and status metrics for all Agents.
    Used for the Accounts Overview table/chart.
    """
    repo = AnalyticsRepository(db)
    summary = repo.get_agent_performance_summary()
    return {"data": summary, "count": len(summary)}

@router.get("/orders/summary")
def get_orders_summary(db: Session = Depends(get_db)):
    """
    Retrieves progress and status metrics for all Orders.
    Used for the Orders Overview table/chart.
    """
    repo = AnalyticsRepository(db)
    summary = repo.get_order_progress_summary()
    return {"data": summary, "count": len(summary)}

@router.get("/orders/{order_id}/retention")
def get_order_retention(order_id: int, db: Session = Depends(get_db)):
    """
    Calculates retention statistics (added vs. left) for a specific Order/Target Group.
    Requires the MemberMovement table to be populated by the background service.
    """
    repo = AnalyticsRepository(db)
    retention_data = repo.get_member_retention_summary(order_id)
    return retention_data

# Include the defined router into the main app instance
app.include_router(router)