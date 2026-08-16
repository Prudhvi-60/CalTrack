import pytest

from app.core.config import Settings, validate_production_settings
from app.core.database_url import engine_kwargs, sqlalchemy_database_url, uses_transaction_pooler


def test_postgres_scheme_becomes_psycopg() -> None:
    url = sqlalchemy_database_url("postgres://user:pass@db.example.com:5432/postgres")
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in url


def test_railway_private_url_does_not_force_ssl() -> None:
    url = sqlalchemy_database_url("postgresql://postgres:pass@postgres.railway.internal:5432/railway")
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode" not in url


def test_railway_public_url_requires_ssl() -> None:
    url = sqlalchemy_database_url("postgresql://postgres:pass@switchyard.proxy.rlwy.net:12345/railway")
    assert "sslmode=require" in url


def test_supabase_transaction_pooler_uses_null_pool() -> None:
    url = sqlalchemy_database_url("postgresql://user:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres")
    assert "sslmode=require" in url
    assert uses_transaction_pooler(url)
    kwargs = engine_kwargs(url, pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800)
    assert kwargs["poolclass"].__name__ == "NullPool"
    assert kwargs["connect_args"]["prepare_threshold"] is None


def test_supabase_session_pooler_keeps_sqlalchemy_pool() -> None:
    url = sqlalchemy_database_url("postgresql://user:pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres")
    assert "sslmode=require" in url
    assert uses_transaction_pooler(url) is False
    kwargs = engine_kwargs(url, pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800)
    assert "poolclass" not in kwargs
    assert kwargs["pool_size"] == 5


def test_supabase_direct_host_requires_ssl() -> None:
    url = sqlalchemy_database_url("postgresql://postgres:pass@db.abcdefgh.supabase.co:5432/postgres")
    assert url.startswith("postgresql+psycopg://")
    assert "sslmode=require" in url


def test_supabase_database_url_alias(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.setenv(
        "SUPABASE_DATABASE_URL",
        "postgresql://postgres:pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres",
    )
    settings = Settings(_env_file=None)
    assert "pooler.supabase.com" in settings.database_url


def test_production_cookies_are_secure_cross_site() -> None:
    settings = Settings(environment="production", cookie_samesite="lax", cookie_secure=False)
    assert settings.refresh_cookie_secure is True
    assert settings.refresh_cookie_samesite == "none"


def test_development_cookies_stay_lax() -> None:
    settings = Settings(environment="development", cookie_samesite="lax", cookie_secure=False)
    assert settings.refresh_cookie_secure is False
    assert settings.refresh_cookie_samesite == "lax"


def test_ai_configured_flag_does_not_require_printing_the_key() -> None:
    assert Settings(_env_file=None, ai_api_key="").ai_configured is False
    assert Settings(_env_file=None, ai_api_key="sk-test").ai_configured is True
    assert Settings(_env_file=None, ai_api_key="sk-test").ai_provider_name == "Gemini"


def test_gemini_api_key_env_alias(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    settings = Settings()
    assert settings.ai_configured is True
    assert settings.ai_api_key == "gemini-test-key"


def test_development_always_includes_local_vite_origins() -> None:
    settings = Settings(
        frontend_url="http://localhost:5173",
        cors_origins="http://127.0.0.1:8001",
        _env_file=None,
    )
    assert "http://localhost:5173" in settings.cors_origin_list
    assert "http://127.0.0.1:5173" in settings.cors_origin_list
    assert "http://127.0.0.1:8001" in settings.cors_origin_list


def test_cors_includes_frontend_url_and_rejects_wildcard() -> None:
    settings = Settings(
        frontend_url="https://app.example.com",
        cors_origins="http://localhost:5173, *",
        _env_file=None,
    )
    assert "https://app.example.com" in settings.cors_origin_list
    assert "*" not in settings.cors_origin_list


def test_production_cors_uses_frontend_url_not_localhost_defaults() -> None:
    settings = Settings(
        environment="production",
        frontend_url="https://app.example.com",
        cors_origins="http://localhost:5173,http://127.0.0.1:5173",
        jwt_secret_key="a-secure-production-jwt-secret-key!!",
        database_url="postgresql+psycopg://user:pass@db.example.com:5432/caltrack",
        _env_file=None,
    )
    assert settings.cors_origin_list == ["https://app.example.com"]


def test_production_settings_require_secrets() -> None:
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="change-me-to-a-long-random-secret",
                database_url="postgresql+psycopg://caltrack:caltrack@localhost:5432/caltrack",
                frontend_url="https://app.example.com",
                cors_origins="",
            )
        )
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="a-secure-production-jwt-secret-key!!",
                database_url="postgresql+psycopg://caltrack:caltrack@localhost:5432/caltrack",
                frontend_url="https://app.example.com",
                cors_origins="https://app.example.com",
            )
        )
    with pytest.raises(RuntimeError, match="FRONTEND_URL"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="a-secure-production-jwt-secret-key!!",
                database_url="postgresql+psycopg://user:pass@db.example.com:5432/caltrack",
                frontend_url="http://localhost:5173",
                cors_origins="http://localhost:5173,http://127.0.0.1:5173",
            )
        )


def test_production_rejects_short_jwt_and_sqlite() -> None:
    with pytest.raises(RuntimeError, match="32 characters"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="too-short-to-be-production",
                database_url="postgresql+psycopg://user:pass@db.example.com:5432/caltrack",
                frontend_url="https://app.example.com",
                cors_origins="https://app.example.com",
                ai_provider="Gemini",
            )
        )
    with pytest.raises(RuntimeError, match="SQLite"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="a-secure-production-jwt-secret-key!!",
                database_url="sqlite:///./caltrack.db",
                frontend_url="https://app.example.com",
                cors_origins="https://app.example.com",
                ai_provider="Gemini",
            )
        )
    with pytest.raises(RuntimeError, match="Gemini"):
        validate_production_settings(
            Settings.model_construct(
                environment="production",
                jwt_secret_key="a-secure-production-jwt-secret-key!!",
                database_url="postgresql+psycopg://user:pass@db.example.com:5432/caltrack",
                frontend_url="https://app.example.com",
                cors_origins="https://app.example.com",
                ai_provider="grok",
            )
        )


def test_sqlite_urls_are_rejected() -> None:
    with pytest.raises(ValueError, match="SQLite"):
        sqlalchemy_database_url("sqlite:///./caltrack.db")


def test_settings_load_without_env_file() -> None:
    settings = Settings(_env_file=None)
    assert settings.environment == "development"
    assert settings.frontend_url
    assert settings.jwt_secret_key
