# app/services/health.py
import socket
import socks
from datetime import datetime
from sqlalchemy import text
from app.repositories.settings_repo import SettingsRepository
from app.core import config
from app.core.telegram_proxy import get_proxy

_WORKER_HEARTBEAT_KEY = "_worker_heartbeat_at"
_TELEGRAM_REACHABLE_KEY = "_telegram_reachable"
_TELEGRAM_CHECKED_AT_KEY = "_telegram_checked_at"

WORKER_STALE_AFTER_SECONDS = 30
TELEGRAM_RECHECK_INTERVAL_SECONDS = 60

# A well-known Telegram MTProto data center IP — used only for a plain TCP
# reachability probe (no protocol handshake), to detect whether this host's
# network can reach Telegram at all (relevant on networks that block it).
TELEGRAM_PROBE_HOST = "149.154.167.50"
TELEGRAM_PROBE_PORT = 443


def record_worker_heartbeat(db):
    SettingsRepository(db).set_setting(_WORKER_HEARTBEAT_KEY, datetime.utcnow().isoformat())


def probe_telegram_reachable(timeout: float = 5.0) -> bool:
    """Mirrors exactly how Telethon will actually connect — through the local
    Xray-core SOCKS5 proxy if TELEGRAM_PROXIES is configured, direct otherwise."""
    proxy = get_proxy()
    try:
        if proxy:
            _, host, port = proxy
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, host, port)
            s.settimeout(timeout)
            s.connect((TELEGRAM_PROBE_HOST, TELEGRAM_PROBE_PORT))
            s.close()
        else:
            with socket.create_connection((TELEGRAM_PROBE_HOST, TELEGRAM_PROBE_PORT), timeout=timeout):
                pass
        return True
    except OSError:
        return False


def should_recheck_telegram(db) -> bool:
    checked_at = SettingsRepository(db).get_setting(_TELEGRAM_CHECKED_AT_KEY)
    if not checked_at:
        return True
    age = (datetime.utcnow() - datetime.fromisoformat(checked_at)).total_seconds()
    return age >= TELEGRAM_RECHECK_INTERVAL_SECONDS


def record_telegram_reachability(db, reachable: bool):
    repo = SettingsRepository(db)
    repo.set_setting(_TELEGRAM_REACHABLE_KEY, "true" if reachable else "false")
    repo.set_setting(_TELEGRAM_CHECKED_AT_KEY, datetime.utcnow().isoformat())


def get_status(db) -> dict:
    repo = SettingsRepository(db)
    status = {"api": "ok", "telegram_proxy_count": len(config.TELEGRAM_PROXIES)}

    try:
        db.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception:
        status["database"] = "error"

    heartbeat_raw = repo.get_setting(_WORKER_HEARTBEAT_KEY)
    if heartbeat_raw:
        age = (datetime.utcnow() - datetime.fromisoformat(heartbeat_raw)).total_seconds()
        status["worker"] = "ok" if age <= WORKER_STALE_AFTER_SECONDS else "stale"
    else:
        status["worker"] = "unknown"
    status["worker_last_heartbeat"] = heartbeat_raw

    telegram_raw = repo.get_setting(_TELEGRAM_REACHABLE_KEY)
    status["telegram_reachable"] = (telegram_raw == "true") if telegram_raw is not None else None
    status["telegram_checked_at"] = repo.get_setting(_TELEGRAM_CHECKED_AT_KEY)

    return status
