import asyncio
import pytest
from telethon.errors import SessionPasswordNeededError
from app.modules.auth.service import AuthService, PENDING_LOGIN_CLIENTS
from app.models.agent import Agent


class FakeMe:
    id = 999111


class FakeSession:
    def save(self):
        return "fake-session-string"


class FakeClient:
    """Stands in for Telethon's TelegramClient — enough surface for
    AuthService.verify_code/verify_password without a real network call."""

    def __init__(self, requires_password=False):
        self.requires_password = requires_password
        self.session = FakeSession()
        self.disconnected = False

    async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
        if password is None and self.requires_password:
            raise SessionPasswordNeededError(request=None)

    async def get_me(self):
        return FakeMe()

    async def disconnect(self):
        self.disconnected = True


def test_verify_code_propagates_session_password_needed(db_session):
    phone = "+989120000001"
    PENDING_LOGIN_CLIENTS[phone] = {"client": FakeClient(requires_password=True), "phone_code_hash": "h", "api_id": "1", "api_hash": "a"}

    service = AuthService()
    with pytest.raises(SessionPasswordNeededError):
        asyncio.run(service.verify_code(phone, "12345", db_session))

    # Pending context must survive so verify_password() can resume the same login.
    assert phone in PENDING_LOGIN_CLIENTS
    del PENDING_LOGIN_CLIENTS[phone]


def test_verify_password_completes_login_and_saves_agent(db_session):
    phone = "+989120000002"
    PENDING_LOGIN_CLIENTS[phone] = {"client": FakeClient(requires_password=True), "phone_code_hash": "h", "api_id": "111", "api_hash": "aaa"}

    service = AuthService()
    asyncio.run(service.verify_password(phone, "my-cloud-password", db_session))

    assert phone not in PENDING_LOGIN_CLIENTS
    agent = db_session.query(Agent).filter(Agent.phone == phone).first()
    assert agent is not None
    assert agent.session_string == "fake-session-string"
    assert agent.is_active is True


def test_verify_password_without_pending_login_raises(db_session):
    service = AuthService()
    with pytest.raises(Exception):
        asyncio.run(service.verify_password("+989120009999", "x", db_session))
