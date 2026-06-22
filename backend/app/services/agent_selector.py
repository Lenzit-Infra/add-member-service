# app/services/agent_selector.py
"""
Centralized agent-eligibility / load-balancing logic, shared by the worker
(who gets the next batch) and analytics (what does each agent's Telegram
capacity look like right now). Single source of truth so the two never
disagree about what "available" means.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.agent import Agent
from app.models.logs import OperationLog, OperationStatus


def get_today_start() -> datetime:
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def get_today_counts(db: Session) -> Dict[int, int]:
    """agent_id -> number of SUCCESSful adds since UTC midnight. Computed from
    OperationLog (the source of truth) rather than a stored counter, so it's
    always correct and never needs an explicit daily-reset job."""
    rows = (
        db.query(OperationLog.agent_id, func.count(OperationLog.id))
        .filter(OperationLog.status == OperationStatus.SUCCESS, OperationLog.timestamp >= get_today_start())
        .group_by(OperationLog.agent_id)
        .all()
    )
    return {agent_id: count for agent_id, count in rows}


def get_recent_failure_ratio(db: Session, agent_id: int, sample: int = 10) -> float:
    """Fraction of the agent's last `sample` operations that failed. A soft
    'needs review' signal for the UI — never auto-bans an agent."""
    recent = (
        db.query(OperationLog.status)
        .filter(OperationLog.agent_id == agent_id)
        .order_by(OperationLog.timestamp.desc())
        .limit(sample)
        .all()
    )
    if not recent:
        return 0.0
    failures = sum(1 for (status,) in recent if status != OperationStatus.SUCCESS)
    return failures / len(recent)


def _eligible_candidates(db: Session) -> List[Agent]:
    now = datetime.utcnow()
    return (
        db.query(Agent)
        .filter(Agent.is_active == True, Agent.is_banned == False)
        .filter((Agent.cooldown_until.is_(None)) | (Agent.cooldown_until <= now))
        .all()
    )


def daily_limit_for(agent: Agent, new_agent_limit: int, steady_limit: int, warmup_days: int) -> int:
    """Telegram doesn't publish fixed thresholds, but newer/unproven accounts
    are well-documented to draw stricter scrutiny — so a brand-new agent
    starts at `new_agent_limit` and ramps linearly up to `steady_limit` over
    `warmup_days`, based on how long it's actually been onboarded."""
    if warmup_days <= 0 or not agent.first_joined_at or new_agent_limit >= steady_limit:
        return steady_limit
    age_days = (datetime.utcnow() - agent.first_joined_at).total_seconds() / 86400
    if age_days >= warmup_days:
        return steady_limit
    progress = max(0.0, age_days) / warmup_days
    return max(1, round(new_agent_limit + (steady_limit - new_agent_limit) * progress))


def select_best_agent(db: Session, daily_limit: int, new_agent_daily_limit: Optional[int] = None, warmup_days: int = 0) -> Optional[Agent]:
    """The actual anti-ban assignment rule: among active, non-banned,
    not-in-flood-cooldown, under-(age-aware)-daily-limit agents, pick the one
    used the LEAST today. This spreads volume across the whole pool instead
    of draining one account first — keeping any single account's daily add
    volume low is the single biggest lever against Telegram flagging it."""
    today_counts = get_today_counts(db)
    new_limit = new_agent_daily_limit if new_agent_daily_limit is not None else daily_limit
    eligible = [
        a for a in _eligible_candidates(db)
        if today_counts.get(a.id, 0) < daily_limit_for(a, new_limit, daily_limit, warmup_days)
    ]
    if not eligible:
        return None
    eligible.sort(key=lambda a: today_counts.get(a.id, 0))
    return eligible[0]


def count_eligible_agents(db: Session, daily_limit: int, new_agent_daily_limit: Optional[int] = None, warmup_days: int = 0) -> int:
    today_counts = get_today_counts(db)
    new_limit = new_agent_daily_limit if new_agent_daily_limit is not None else daily_limit
    return sum(
        1 for a in _eligible_candidates(db)
        if today_counts.get(a.id, 0) < daily_limit_for(a, new_limit, daily_limit, warmup_days)
    )


def agent_status_info(db: Session, agent: Agent, daily_limit: int, today_counts: Optional[Dict[int, int]] = None, needs_review_ratio: float = 0.7) -> Dict[str, Any]:
    """Everything the Agents/Dashboard UI needs to answer 'what's this agent's
    Telegram status, and when does it free up again?'"""
    counts = today_counts if today_counts is not None else get_today_counts(db)
    today_count = counts.get(agent.id, 0)
    now = datetime.utcnow()

    in_cooldown = bool(agent.cooldown_until and agent.cooldown_until > now)
    capacity_full = today_count >= daily_limit

    if agent.is_banned:
        state = "banned"
    elif not agent.is_active:
        state = "idle"
    elif in_cooldown:
        state = "cooldown"
    elif capacity_full:
        state = "capacity_full"
    else:
        state = "available"

    next_midnight = get_today_start() + timedelta(days=1)
    resets_at = None
    if in_cooldown and agent.cooldown_until > next_midnight:
        resets_at = agent.cooldown_until
    elif capacity_full or in_cooldown:
        resets_at = next_midnight

    return {
        "agent_id": agent.id,
        "state": state,
        "today_count": today_count,
        "daily_limit": daily_limit,
        "resets_at": resets_at.isoformat() if resets_at else None,
        "needs_review": get_recent_failure_ratio(db, agent.id) >= needs_review_ratio,
        "pause_reason": agent.pause_reason,
    }
