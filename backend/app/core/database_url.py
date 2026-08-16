from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.pool import NullPool

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def sqlalchemy_database_url(raw: str) -> str:
    """Normalize provider URLs for SQLAlchemy + psycopg3. Do not change host or credentials."""
    url = (raw or "").strip()
    if not url:
        raise ValueError("DATABASE_URL is not configured")
    if url.lower().startswith("sqlite"):
        raise ValueError("SQLite is not supported; set DATABASE_URL to PostgreSQL")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return _ensure_sslmode(url)


def database_hostname(raw: str) -> str:
    url = (raw or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return (urlsplit(url).hostname or "").lower()


def is_unconfigured_database_url(raw: str | None) -> bool:
    """True when the value is missing, an unresolved Railway template, or a local fallback."""
    text = (raw or "").strip()
    if not text:
        return True
    if "${{" in text or text.startswith("${"):
        return True
    host = database_hostname(text)
    if not host or host in _LOCAL_HOSTS:
        return True
    return False


def _ensure_sslmode(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    local = host in _LOCAL_HOSTS or host.endswith(".local")
    railway_private = host.endswith(".railway.internal")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if not local and not railway_private and "sslmode" not in {key.lower() for key in query}:
        query["sslmode"] = "require"
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    return url


def uses_transaction_pooler(url: str) -> bool:
    """Supabase transaction-mode pooler (port 6543) does not support prepared statements."""
    return urlsplit(url).port == 6543


def engine_kwargs(url: str, *, pool_size: int, max_overflow: int, pool_timeout: int, pool_recycle: int) -> dict:
    connect_args: dict = {}
    if uses_transaction_pooler(url):
        connect_args["prepare_threshold"] = None
        return {
            "poolclass": NullPool,
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }
    return {
        "pool_pre_ping": True,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_recycle": pool_recycle,
        "connect_args": connect_args,
    }
