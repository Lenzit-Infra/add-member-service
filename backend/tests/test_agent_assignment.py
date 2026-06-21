from datetime import datetime, timedelta
from app.models.agent import Agent
from app.models.logs import OperationLog, OperationStatus
from app.services import agent_selector

DAILY_LIMIT = 10


def _make_agent(db, phone, user_id, is_active=True, is_banned=False, cooldown_until=None):
    agent = Agent(
        api_id="1", api_hash="hash", phone=phone, session_string="sess",
        user_id=user_id, is_active=is_active, is_banned=is_banned, cooldown_until=cooldown_until,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def _log_successes(db, agent_id, count, when=None):
    when = when or datetime.utcnow()
    for _ in range(count):
        db.add(OperationLog(agent_id=agent_id, status=OperationStatus.SUCCESS, timestamp=when))
    db.commit()


def test_selects_least_used_agent_today(db_session):
    busy = _make_agent(db_session, "+1000", 1000)
    idle = _make_agent(db_session, "+1001", 1001)
    _log_successes(db_session, busy.id, 5)
    _log_successes(db_session, idle.id, 1)

    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen.id == idle.id


def test_skips_banned_agent(db_session):
    banned = _make_agent(db_session, "+1002", 1002, is_banned=True)
    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen is None or chosen.id != banned.id


def test_skips_inactive_agent(db_session):
    _make_agent(db_session, "+1003", 1003, is_active=False)
    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen is None


def test_skips_agent_in_flood_cooldown(db_session):
    in_cooldown = _make_agent(db_session, "+1004", 1004, cooldown_until=datetime.utcnow() + timedelta(minutes=30))
    available = _make_agent(db_session, "+1005", 1005)

    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen.id == available.id


def test_expired_cooldown_agent_is_eligible_again(db_session):
    agent = _make_agent(db_session, "+1006", 1006, cooldown_until=datetime.utcnow() - timedelta(minutes=1))
    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen.id == agent.id


def test_agent_at_daily_limit_is_excluded(db_session):
    maxed = _make_agent(db_session, "+1007", 1007)
    _log_successes(db_session, maxed.id, DAILY_LIMIT)  # exactly at the limit

    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen is None


def test_yesterdays_adds_dont_count_toward_todays_limit(db_session):
    agent = _make_agent(db_session, "+1008", 1008)
    yesterday = datetime.utcnow() - timedelta(days=1)
    _log_successes(db_session, agent.id, DAILY_LIMIT, when=yesterday)  # all from yesterday

    chosen = agent_selector.select_best_agent(db_session, DAILY_LIMIT)
    assert chosen.id == agent.id  # today's count is 0, so it's eligible


def test_agent_status_info_reports_capacity_full(db_session):
    agent = _make_agent(db_session, "+1009", 1009)
    _log_successes(db_session, agent.id, DAILY_LIMIT)

    info = agent_selector.agent_status_info(db_session, agent, DAILY_LIMIT)
    assert info["state"] == "capacity_full"
    assert info["resets_at"] is not None


def test_agent_status_info_reports_cooldown(db_session):
    until = datetime.utcnow() + timedelta(hours=2)
    agent = _make_agent(db_session, "+1010", 1010, cooldown_until=until)

    info = agent_selector.agent_status_info(db_session, agent, DAILY_LIMIT)
    assert info["state"] == "cooldown"


def test_count_eligible_agents(db_session):
    _make_agent(db_session, "+1011", 1011)
    _make_agent(db_session, "+1012", 1012, is_banned=True)
    _make_agent(db_session, "+1013", 1013)

    assert agent_selector.count_eligible_agents(db_session, DAILY_LIMIT) == 2
