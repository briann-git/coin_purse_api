"""Shared pytest fixtures for the Coin Purse API test suite.

Strategy
--------
- One in-memory SQLite database is created per test *session* (schema built once).
- Each test runs inside a transaction that is **rolled back** at teardown, keeping
  tests fully isolated without the cost of recreating all tables.
- `get_db` is overridden via FastAPI's dependency system so all routes use the
  same transactional session.
- `transaction_kinds` rows are seeded once at session scope because they are
  lookup data that every transaction test depends on.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from common.db.config import get_db
from helpers.seed_data import seed_transaction_kinds
from main import app
from models.models import Base

# ---------------------------------------------------------------------------
# Engine / schema — session-scoped (built once for the whole test run)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Seed lookup data once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def seed_kinds(session_factory):
    """Insert the four TransactionKind rows once; they survive across all tests."""
    db = session_factory()
    try:
        seed_transaction_kinds(db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Per-test transactional isolation
# ---------------------------------------------------------------------------


@pytest.fixture
def db(engine, session_factory):
    """Each test gets its own connection wrapped in a savepoint.

    The outer transaction is rolled back after the test so no data leaks between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()

    bound_session = session_factory(bind=connection)

    # Nested savepoint so code under test can call commit() without ending
    # the outer transaction we intend to roll back.
    connection.begin_nested()

    yield bound_session

    bound_session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session):
    """TestClient with get_db overridden to use the isolated test session."""

    def override_get_db():
        try:
            yield db
        finally:
            pass  # teardown handled by the `db` fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(client: TestClient) -> dict:
    """Create and return a test user."""
    res = client.post(
        "/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "TestPass123!",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
def user_id(user: dict) -> str:
    return user["id"]
