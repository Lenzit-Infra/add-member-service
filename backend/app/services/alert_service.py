# app/services/alert_service.py
import logging
import httpx
from app.core import config
from app.core.telegram_proxy import get_proxy

logger = logging.getLogger("watchdog")


def send_owner_alert(message: str) -> bool:
    """DMs the owner via a Telegram bot (api.telegram.org) when configured.
    Routed through the same local Xray SOCKS5 proxy as everything else Telegram-
    related, since this network blocks Telegram's domains/IPs directly too."""
    if not config.ALERT_BOT_TOKEN or not config.ALERT_CHAT_ID:
        return False

    proxy = get_proxy()
    proxy_url = f"socks5://{proxy[1]}:{proxy[2]}" if proxy else None

    try:
        with httpx.Client(proxy=proxy_url, timeout=15) as client:
            resp = client.post(
                f"https://api.telegram.org/bot{config.ALERT_BOT_TOKEN}/sendMessage",
                json={"chat_id": config.ALERT_CHAT_ID, "text": message},
            )
            resp.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send down-alert via Telegram Bot API")
        return False
