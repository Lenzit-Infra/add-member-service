import os
import sys

# backend/ root must be on sys.path so "app.*" resolves regardless of how pytest is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_session_factory(tmp_path_factory):
    """One isolated SQLite file for the whole test session — points the app's
    database module at it instead of the real bot_database.db."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    from app.core import database
    database.engine = engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database.SessionLocal = TestingSessionLocal

    from app.models import agent, group, member, order, logs, settings, user, audit_log  # noqa: registers all tables
    database.Base.metadata.create_all(bind=engine)

    from app.core import config
    config.ADMIN_EMAILS = ["admin@example.com"]
    config.COOKIE_SECURE = False  # TestClient talks over plain http://testserver
    config.COOKIE_DOMAIN = None  # ".lenzit.ir" wouldn't match the "testserver" host, so httpx would drop the cookie

    return TestingSessionLocal


@pytest.fixture(scope="session")
def app(test_session_factory):
    from app.main import app as fastapi_app
    from app.core.database import get_db
    from fastapi import Header, Depends
    from sqlalchemy.orm import Session
    from app.modules.account.dependencies import get_current_user
    from app.models.user import User

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user(
        x_test_role: str = Header(default=None),
        x_test_user_id: str = Header(default=None),
        authorization: str = Header(default=None),
        db: Session = Depends(get_db),
    ):
        # Identity comes from per-request headers (set as default headers on each
        # TestClient instance), not from app.dependency_overrides — that dict is
        # shared by every TestClient bound to this session-scoped app, so keying
        # identity off it breaks as soon as a test needs two different "logged in
        # as" clients at once (e.g. an admin client + an operator client). Tests
        # that exercise the real auth flow (login/refresh/JWT) send no test
        # headers at all, so they fall through to the real implementation.
        if x_test_role is not None:
            return User(id=int(x_test_user_id or 999999), username=f"test_{x_test_role}", email=f"{x_test_role}@example.com", password_hash="x", role=x_test_role)
        return get_current_user(authorization=authorization, db=db)

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    return fastapi_app


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def authed_client(app):
    """A client where the dashboard-login gate is bypassed (acting as an admin) —
    for tests that exercise business logic (orders/agents/etc.), not the auth flow itself."""
    return TestClient(app, headers={"x-test-role": "admin", "x-test-user-id": "999999"})


@pytest.fixture()
def role_client(app):
    """Factory fixture: role_client('operator') -> TestClient acting as a user
    with that role. Independent of authed_client — each TestClient carries its
    own identity via headers, so both can be used in the same test."""
    def _factory(role: str, user_id: int = 900000):
        return TestClient(app, headers={"x-test-role": role, "x-test-user-id": str(user_id)})
    return _factory


@pytest.fixture()
def db_session(test_session_factory):
    db = test_session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_db(test_session_factory):
    """Wipe all table data after every test so tests don't leak state into each other."""
    yield
    from app.core.database import Base
    db = test_session_factory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
