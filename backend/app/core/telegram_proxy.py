# app/core/telegram_proxy.py
import socks
from app.core import config


def get_proxy():
    """Telethon `proxy=` tuple pointing at the local Xray-core SOCKS5 inbound,
    or None if no proxying is configured at all (direct connection). Xray
    itself fans out to every link from TELEGRAM_PROXY_SUBSCRIPTION_URL (or the
    static TELEGRAM_PROXIES fallback) and routes through whichever has the
    best live ping — this is just the local hop, so it only needs to know
    whether proxying is configured, not which links are currently live."""
    if not (config.TELEGRAM_PROXY_SUBSCRIPTION_URL or config.TELEGRAM_PROXIES):
        return None
    return (socks.SOCKS5, "127.0.0.1", config.TELEGRAM_PROXY_SOCKS_PORT)
