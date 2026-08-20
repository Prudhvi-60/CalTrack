from __future__ import annotations

import os
import socket

os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production-use-32")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-not-for-production")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5174")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


def _reachable(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


if "DATABASE_URL" not in os.environ:
    if _reachable(5433):
        os.environ["DATABASE_URL"] = "postgresql+psycopg://vitaphiles:vitaphiles@127.0.0.1:5433/vitaphiles"
    elif _reachable(5432):
        os.environ["DATABASE_URL"] = "postgresql+psycopg://vitaphiles:vitaphiles@127.0.0.1:5432/vitaphiles"
    else:
        os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.database import engine
from app.db.session import get_db
import app.models  # noqa: F401
from app.main import app


@pytest.fixture(autouse=True)
def _disable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.rate_limit.limiter.allow", lambda *_args, **_kwargs: True)


@pytest.fixture(scope="session", autouse=True)
def _create_sqlite_schema() -> None:
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)


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
