import math
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models.agent import Agent
from app.models.order import Order, OrderSourceGroup, OrderStatus
from app.models.logs import OperationLog, MemberMovement, OperationStatus
from app.models.group import Group
from app.models.member import Member
from app.repositories.settings_repo import SettingsRepository
from app.services import agent_selector
from typing import List, Dict, Any, Optional

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

    def get_agent_performance_summary(self) -> List[Dict[str, Any]]:
        """Per-agent stats + live Telegram-capacity status (answers 'what's
        this agent's status, and when does its capacity free up?')."""
        daily_limit = int(SettingsRepository(self.db).get_setting("daily_limit_per_agent", "30"))
        agents = self.db.query(Agent).all()
        today_counts = agent_selector.get_today_counts(self.db)

        result = []
        for agent in agents:
            capacity = agent_selector.agent_status_info(self.db, agent, daily_limit, today_counts)
            result.append({
                "id": agent.id,
                "phone": agent.phone,
                "is_active": agent.is_active,
                "is_banned": agent.is_banned,
                "ban_reason": agent.ban_reason,
                "first_joined_at": agent.first_joined_at.strftime("%Y-%m-%d") if agent.first_joined_at else "-",
                "last_active_at": agent.last_active_at.strftime("%Y-%m-%d %H:%M") if agent.last_active_at else "-",
                "total_active_seconds": agent.total_active_seconds,
                "total_adds": agent.total_adds,
                # Live capacity (replaces the never-reset daily_adds counter)
                "today_adds": capacity["today_count"],
                "daily_limit": capacity["daily_limit"],
                "state": capacity["state"],  # available | capacity_full | cooldown | idle | banned
                "resets_at": capacity["resets_at"],
                "needs_review": capacity["needs_review"],
            })
        return result

    def get_agent_history(self, agent_id: int, limit: int = 300) -> List[Dict[str, Any]]:
        """Full operation history for one agent — every add attempt, dated."""
        logs = (
            self.db.query(OperationLog)
            .filter(OperationLog.agent_id == agent_id)
            .order_by(desc(OperationLog.timestamp))
            .limit(limit)
            .all()
        )
        return [
            {
                "id": log.id,
                "order_id": log.order_id,
                "target_group": log.target_group.title if log.target_group else None,
                "member_id": str(log.member_id) if log.member_id else None,
                "username": log.member.username if log.member else None,
                "status": log.status.value if log.status else None,
                "fail_reason": log.fail_reason,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "-",
            }
            for log in logs
        ]

    def get_capacity_planning(self) -> Dict[str, Any]:
        """Answers: what's each active order's status/blocker/ETA, and how many
        agents would it take to clear the whole backlog at today's pace?"""
        daily_limit = int(SettingsRepository(self.db).get_setting("daily_limit_per_agent", "30"))
        eligible_agent_count = agent_selector.count_eligible_agents(self.db, daily_limit)
        total_agents = self.db.query(Agent).count()
        banned_count = self.db.query(Agent).filter(Agent.is_banned == True).count()

        active_orders = (
            self.db.query(Order)
            .filter(Order.status.in_([OrderStatus.PENDING_AGENT, OrderStatus.IN_PROGRESS, OrderStatus.PAUSED]))
            .order_by(desc(Order.created_at))
            .all()
        )

        order_rows = []
        total_remaining = 0
        for order in active_orders:
            remaining = max(0, order.desired_count - order.current_count)
            total_remaining += remaining if order.status != OrderStatus.PAUSED else 0

            if order.status == OrderStatus.PAUSED:
                blocking_reason = "Paused by admin"
            elif eligible_agent_count == 0:
                if total_agents == 0:
                    blocking_reason = "No agents configured yet"
                elif banned_count == total_agents:
                    blocking_reason = "All agents are banned"
                else:
                    blocking_reason = "All agents are at today's capacity or in flood-wait cooldown"
            else:
                blocking_reason = "Running normally"

            worst_case_days = math.ceil(remaining / daily_limit) if remaining > 0 and daily_limit > 0 else 0
            best_case_days = (
                math.ceil(remaining / (daily_limit * eligible_agent_count))
                if remaining > 0 and eligible_agent_count > 0 else worst_case_days
            )

            order_rows.append({
                "id": order.id,
                "target_group": order.target_group.title if order.target_group else "Unknown",
                "status": order.status.value,
                "desired_count": order.desired_count,
                "current_count": order.current_count,
                "remaining": remaining,
                "progress_percent": round((order.current_count / order.desired_count) * 100, 1) if order.desired_count > 0 else 0,
                "blocking_reason": blocking_reason,
                "worst_case_days": worst_case_days,
                "best_case_days": best_case_days,
            })

        agents_needed_for_one_day_clear = math.ceil(total_remaining / daily_limit) if daily_limit > 0 else 0
        days_to_clear_with_current_agents = (
            math.ceil(total_remaining / (daily_limit * eligible_agent_count))
            if total_remaining > 0 and eligible_agent_count > 0 else (0 if total_remaining == 0 else None)
        )

        return {
            "orders": order_rows,
            "total_remaining": total_remaining,
            "eligible_agent_count": eligible_agent_count,
            "agents_needed_for_one_day_clear": agents_needed_for_one_day_clear,
            "days_to_clear_with_current_agents": days_to_clear_with_current_agents,
        }

    def get_summary_totals(self) -> Dict[str, Any]:
        """High-level counters for the Dashboard overview page."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return {
            "total_members": self.db.query(Member).count(),
            "total_groups": self.db.query(Group).count(),
            "total_agents": self.db.query(Agent).count(),
            "active_agents": self.db.query(Agent).filter(Agent.is_active == True, Agent.is_banned == False).count(),
            "active_orders": self.db.query(Order).filter(Order.status.in_([OrderStatus.IN_PROGRESS, OrderStatus.PENDING_AGENT])).count(),
            "finished_orders": self.db.query(Order).filter(Order.status == OrderStatus.FINISHED).count(),
            "adds_today": self.db.query(OperationLog).filter(
                OperationLog.status == OperationStatus.SUCCESS,
                OperationLog.timestamp >= today_start
            ).count(),
        }

    def get_daily_adds_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Successful adds per day for the last N days, for the Dashboard chart."""
        since = datetime.utcnow() - timedelta(days=days - 1)
        since_start = since.replace(hour=0, minute=0, second=0, microsecond=0)

        rows = self.db.query(
            func.date(OperationLog.timestamp).label("day"),
            func.count(OperationLog.id).label("count")
        ).filter(
            OperationLog.status == OperationStatus.SUCCESS,
            OperationLog.timestamp >= since_start
        ).group_by("day").all()

        counts_by_day = {str(r.day): r.count for r in rows}

        result = []
        for i in range(days):
            day = (since_start + timedelta(days=i)).date()
            result.append({"date": str(day), "adds": counts_by_day.get(str(day), 0)})
        return result

    def get_movements(self, group_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Join/leave history (Member Movement Monitor) for the Groups page."""
        query = self.db.query(MemberMovement).order_by(desc(MemberMovement.joined_at))
        if group_id is not None:
            query = query.filter(MemberMovement.group_id == group_id)

        movements = query.limit(limit).all()
        return [
            {
                "id": m.id,
                "member_id": str(m.member_id),
                "username": m.member.username if m.member else None,
                "group_id": str(m.group_id),
                "group_title": m.group.title if m.group else None,
                "joined_at": m.joined_at.strftime("%Y-%m-%d %H:%M") if m.joined_at else "-",
                "left_at": m.left_at.strftime("%Y-%m-%d %H:%M") if m.left_at else None,
                "status": "left" if m.left_at else "joined",
            }
            for m in movements
        ]