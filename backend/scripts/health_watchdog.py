# health_watchdog.py
# Polls /api/v1/health from outside the API process itself (so it keeps
# working even if the API hangs rather than crashing cleanly) and DMs the
# owner via a Telegram bot on every ok<->degraded/down state transition —
# not on every poll, so it doesn't spam once something's already known broken.
import sys
import os
import json
import time
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging_config import setup_logging
setup_logging("watchdog")

import logging
from app.services.alert_service import send_owner_alert
from app.services.health import classify_status

logger = logging.getLogger("watchdog")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(BACKEND_DIR, "logs", "_watchdog_state.json")
HEALTH_URL = "http://localhost:4747/api/v1/health"
CHECK_INTERVAL_SECONDS = 60


def fetch_health():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def load_last_status() -> str:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("last_status", "ok")
    except (OSError, json.JSONDecodeError):
        return "ok"


def save_last_status(status: str):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_status": status}, f)


def main():
    last_status = load_last_status()
    logger.info(f"Health watchdog started — checking every {CHECK_INTERVAL_SECONDS}s (last known status: {last_status}).")

    while True:
        status, issues = classify_status(fetch_health())
        if status != last_status:
            if status == "ok":
                message = "✅ Lenzit backend is back to normal."
            else:
                message = f"⚠️ Lenzit backend is {status.upper()}: {', '.join(issues)}"
            logger.warning(message)
            send_owner_alert(message)
            save_last_status(status)
            last_status = status

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
