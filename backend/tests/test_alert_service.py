from app.core import config
from app.services import alert_service


def test_send_owner_alert_noop_when_not_configured(monkeypatch):
    monkeypatch.setattr(config, "ALERT_BOT_TOKEN", "")
    monkeypatch.setattr(config, "ALERT_CHAT_ID", "")
    assert alert_service.send_owner_alert("test") is False


def test_send_owner_alert_posts_to_telegram_api(monkeypatch):
    monkeypatch.setattr(config, "ALERT_BOT_TOKEN", "123:ABC")
    monkeypatch.setattr(config, "ALERT_CHAT_ID", "999")
    monkeypatch.setattr(alert_service, "get_proxy", lambda: None)

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, proxy=None, timeout=None):
            captured["proxy"] = proxy

        def post(self, url, json=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(alert_service.httpx, "Client", FakeClient)

    assert alert_service.send_owner_alert("hello") is True
    assert captured["url"] == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert captured["json"] == {"chat_id": "999", "text": "hello"}
    assert captured["proxy"] is None
