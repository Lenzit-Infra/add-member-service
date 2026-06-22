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


# --- Warm-up ramp (new agents get a lower daily cap that ramps up over time) ---

NEW_AGENT_LIMIT = 5
STEADY_LIMIT = 30
WARMUP_DAYS = 10


def test_daily_limit_for_brand_new_agent_is_the_new_agent_limit(db_session):
    agent = _make_agent(db_session, "+2000", 2000)
    agent.first_joined_at = datetime.utcnow()
    limit = agent_selector.daily_limit_for(agent, NEW_AGENT_LIMIT, STEADY_LIMIT, WARMUP_DAYS)
    assert limit == NEW_AGENT_LIMIT


def test_daily_limit_for_ramps_linearly_midway_through_warmup(db_session):
    agent = _make_agent(db_session, "+2001", 2001)
    agent.first_joined_at = datetime.utcnow() - timedelta(days=WARMUP_DAYS / 2)
    limit = agent_selector.daily_limit_for(agent, NEW_AGENT_LIMIT, STEADY_LIMIT, WARMUP_DAYS)
    expected = round(NEW_AGENT_LIMIT + (STEADY_LIMIT - NEW_AGENT_LIMIT) * 0.5)
    assert limit == expected


def test_daily_limit_for_returns_steady_limit_after_warmup_ends(db_session):
    agent = _make_agent(db_session, "+2002", 2002)
    agent.first_joined_at = datetime.utcnow() - timedelta(days=WARMUP_DAYS + 5)
    limit = agent_selector.daily_limit_for(agent, NEW_AGENT_LIMIT, STEADY_LIMIT, WARMUP_DAYS)
    assert limit == STEADY_LIMIT


def test_daily_limit_for_no_ramp_when_warmup_days_is_zero(db_session):
    agent = _make_agent(db_session, "+2003", 2003)
    agent.first_joined_at = datetime.utcnow()
    limit = agent_selector.daily_limit_for(agent, NEW_AGENT_LIMIT, STEADY_LIMIT, 0)
    assert limit == STEADY_LIMIT


def test_select_best_agent_excludes_new_agent_once_it_hits_its_warmup_cap(db_session):
    brand_new = _make_agent(db_session, "+2004", 2004)
    brand_new.first_joined_at = datetime.utcnow()
    db_session.commit()
    _log_successes(db_session, brand_new.id, NEW_AGENT_LIMIT)  # exactly at its warm-up cap

    chosen = agent_selector.select_best_agent(
        db_session, STEADY_LIMIT, new_agent_daily_limit=NEW_AGENT_LIMIT, warmup_days=WARMUP_DAYS
    )
    assert chosen is None  # would NOT be excluded under the flat steady-state limit alone


def test_select_best_agent_still_uses_warmed_up_agent_under_its_higher_cap(db_session):
    veteran = _make_agent(db_session, "+2005", 2005)
    veteran.first_joined_at = datetime.utcnow() - timedelta(days=WARMUP_DAYS + 1)
    db_session.commit()
    _log_successes(db_session, veteran.id, NEW_AGENT_LIMIT)  # past the new-agent cap, fine for a veteran

    chosen = agent_selector.select_best_agent(
        db_session, STEADY_LIMIT, new_agent_daily_limit=NEW_AGENT_LIMIT, warmup_days=WARMUP_DAYS
    )
    assert chosen.id == veteran.id


def test_agent_status_info_respects_needs_review_ratio_param(db_session):
    agent = _make_agent(db_session, "+2006", 2006)
    for _ in range(7):
        db_session.add(OperationLog(agent_id=agent.id, status=OperationStatus.FAILED_OTHER))
    for _ in range(3):
        db_session.add(OperationLog(agent_id=agent.id, status=OperationStatus.SUCCESS))
    db_session.commit()  # 7/10 = 0.7 failure ratio

    lenient = agent_selector.agent_status_info(db_session, agent, DAILY_LIMIT, needs_review_ratio=0.95)
    strict = agent_selector.agent_status_info(db_session, agent, DAILY_LIMIT, needs_review_ratio=0.5)
    assert lenient["needs_review"] is False
    assert strict["needs_review"] is True
