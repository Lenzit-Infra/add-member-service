# app/core/telegram_proxy.py
import socks
from app.core import config


def get_proxy():
    """Telethon `proxy=` tuple pointing at the local Xray-core SOCKS5 inbound,
    or None if no TELEGRAM_PROXIES are configured (direct connection). Xray
    itself fans out to every configured vless/vmess/ss link and routes through
    whichever has the best live ping — this is just the local hop."""
    if not config.TELEGRAM_PROXIES:
        return None
    return (socks.SOCKS5, "127.0.0.1", config.TELEGRAM_PROXY_SOCKS_PORT)
