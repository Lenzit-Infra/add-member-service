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

    from app.models import agent, group, member, order, logs, settings, user  # noqa: registers all tables
    database.Base.metadata.create_all(bind=engine)

    from app.core import config
    config.ADMIN_EMAILS = ["admin@example.com"]

    return TestingSessionLocal


@pytest.fixture(scope="session")
def app(test_session_factory):
    from app.main import app as fastapi_app
    from app.core.database import get_db

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return fastapi_app


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def authed_client(app):
    """A client where the dashboard-login gate is bypassed — for tests that
    exercise business logic (orders/agents/etc.), not the auth flow itself."""
    from app.modules.account.dependencies import get_current_user
    from app.models.user import User

    dummy_user = User(id=999999, username="testadmin", email="admin@example.com", password_hash="x", role="admin")
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield TestClient(app)
    del app.dependency_overrides[get_current_user]


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
