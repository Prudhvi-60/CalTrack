from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

# Force the test suite to a local database before importing app.db.database, whose
# module-level engine is created at import time. Never let pytest use backend/.env
# because it may point at the production Neon database.
_TEST_DATABASE_URL = os.environ.get(
    "CALTRACK_TEST_DATABASE_URL",
    "postgresql+psycopg://caltrack:caltrack@127.0.0.1:5432/caltrack",
)
if make_url(_TEST_DATABASE_URL).host not in {"localhost", "127.0.0.1", "::1"}:
    raise RuntimeError("CALTRACK_TEST_DATABASE_URL must use a loopback PostgreSQL host")
os.environ["CALTRACK_TESTING"] = "1"
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
os.environ["GEMINI_API_KEY"] = "test-key"

from app.db.database import engine
from app.db.session import get_db
from app.main import app


@pytest.fixture(autouse=True)
def _disable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.rate_limit.limiter.allow", lambda *_args, **_kwargs: True)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(_session: Session, _transaction: object) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
