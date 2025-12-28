from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.agent import Agent
from app.models.order import Order, OrderSourceGroup
from app.models.logs import OperationLog, MemberMovement
from app.models.group import Group
from app.models.member import Member
from typing import List, Dict, Any

class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_members(self) -> List[Dict[str, Any]]:
        """Fetch all members for the Members Tab."""
        members = self.db.query(Member).limit(500).all() # Limit for performance, add pagination later
        return [
            {
                "user_id": str(m.user_id),
                "username": m.username,
                "first_name": m.first_name,
                "status": m.status.value if m.status else "unknown",
                "quality_score": m.quality_score,
                "is_premium": m.is_premium,
                "is_bot": m.is_bot
            }
            for m in members
        ]

    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Fetch all groups for the Groups Tab."""
        groups = self.db.query(Group).all()
        return [
            {
                "id": str(g.id),
                "title": g.title,
                "username": g.username,
                "type": g.type,
                "member_count": g.member_count,
                "invite_link": g.invite_link,
                "is_lenzit_admin": g.is_lenzit_admin
            }
            for g in groups
        ]

    def get_order_details(self) -> List[Dict[str, Any]]:
        """Fetch detailed orders with sources and agents info."""
        orders = self.db.query(Order).order_by(desc(Order.created_at)).all()
        result = []
        for order in orders:
            # 1. Fetch Source Groups
            sources = []
            for osg in order.source_groups:
                if osg.group:
                    sources.append({
                        "id": str(osg.group.id),
                        "title": osg.group.title,
                        "link": osg.group.invite_link,
                        "count": osg.group.member_count
                    })
            
            # 2. Fetch Agents who worked on this order (from Logs)
            # We find unique agents who have logs for this order_id
            agent_ids = self.db.query(OperationLog.agent_id).filter(OperationLog.order_id == order.id).distinct().all()
            agents_info = []
            for (aid,) in agent_ids:
                agent = self.db.query(Agent).filter(Agent.id == aid).first()
                if agent:
                    agents_info.append({
                        "id": agent.id,
                        "phone": agent.phone,
                        "total_adds_for_order": self.db.query(OperationLog).filter(OperationLog.order_id==order.id, OperationLog.agent_id==aid, OperationLog.status=='success').count()
                    })

            result.append({
                "id": order.id,
                "target_group": order.target_group.title if order.target_group else "Unknown",
                "status": order.status.value,
                "desired_count": order.desired_count,
                "current_count": order.current_count,
                "progress_percent": round((order.current_count / order.desired_count) * 100, 1) if order.desired_count > 0 else 0,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                "ended_at": "-", # Placeholder, add logic if needed
                "sources": sources,
                "agents": agents_info
            })
        return result

    # ... (Keep get_agent_performance_summary as is) ...
    def get_agent_performance_summary(self) -> List[Dict[str, Any]]:
        # (This remains similar to before, ensuring we expose all new columns)
        agents = self.db.query(Agent).all()
        return [
            {
                "id": agent.id,
                "phone": agent.phone,
                "is_active": agent.is_active,
                "is_banned": agent.is_banned,
                "ban_reason": agent.ban_reason,
                "first_joined_at": agent.first_joined_at.strftime("%Y-%m-%d") if agent.first_joined_at else "-",
                "last_active_at": agent.last_active_at.strftime("%Y-%m-%d %H:%M") if agent.last_active_at else "-",
                "total_active_seconds": agent.total_active_seconds,
                "daily_adds": agent.daily_adds,
                "monthly_adds": agent.monthly_adds,
                "total_adds": agent.total_adds
            }
            for agent in agents
        ]