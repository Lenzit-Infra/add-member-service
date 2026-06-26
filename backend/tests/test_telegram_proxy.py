from app.core import config
from app.core.telegram_proxy import get_proxy


def test_get_proxy_none_when_nothing_configured(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_PROXY_SUBSCRIPTION_URL", "")
    monkeypatch.setattr(config, "TELEGRAM_PROXIES", [])
    assert get_proxy() is None


def test_get_proxy_set_when_subscription_url_configured(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_PROXY_SUBSCRIPTION_URL", "https://example.com/sub")
    monkeypatch.setattr(config, "TELEGRAM_PROXIES", [])
    monkeypatch.setattr(config, "TELEGRAM_PROXY_SOCKS_PORT", 11080)
    assert get_proxy() == (2, "127.0.0.1", 11080)  # socks.SOCKS5 == 2


def test_get_proxy_set_when_only_static_list_configured(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_PROXY_SUBSCRIPTION_URL", "")
    monkeypatch.setattr(config, "TELEGRAM_PROXIES", ["vless://fake"])
    monkeypatch.setattr(config, "TELEGRAM_PROXY_SOCKS_PORT", 11080)
    assert get_proxy() == (2, "127.0.0.1", 11080)
