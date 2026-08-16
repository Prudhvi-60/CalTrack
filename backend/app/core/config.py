from functools import lru_cache
from pathlib import Path
import os

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.database_url import is_unconfigured_database_url

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _settings_env_files() -> tuple[str, ...]:
    # Railway injects real env vars. Never load a packaged .env that points at localhost.
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID"):
        return ()
    return tuple(
        str(path)
        for path in (_REPO_ROOT / ".env", _BACKEND_DIR / ".env")
        if path.is_file()
    )


_DEV_JWT_SECRET = "change-me-to-a-long-random-secret"
_DEV_DATABASE_URL = "postgresql+psycopg://caltrack:caltrack@localhost:5432/caltrack"
_LOCAL_DEV_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_settings_env_files() or None,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
        populate_by_name=True,
    )

    environment: str = Field(default="development", validation_alias=AliasChoices("ENVIRONMENT", "environment"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "log_level"))
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL", "SUPABASE_DATABASE_URL", "POSTGRES_URL", "database_url"),
    )
    railway_environment: str = Field(
        default="",
        validation_alias=AliasChoices("RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME"),
    )
    railway_project_id: str = Field(default="", validation_alias=AliasChoices("RAILWAY_PROJECT_ID"))
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    jwt_secret_key: str = Field(
        default=_DEV_JWT_SECRET,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "jwt_secret_key"),
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    rate_limit_enabled: bool = True
    auth_rate_limit_per_minute: int = 20
    ai_rate_limit_per_minute: int = 10
    ai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "AI_API_KEY", "GOOGLE_API_KEY", "ai_api_key"),
    )
    ai_provider: str = Field(default="Gemini", validation_alias=AliasChoices("AI_PROVIDER", "ai_provider"))
    ai_model: str = Field(default="gemini-3.1-flash-lite", validation_alias=AliasChoices("AI_MODEL", "ai_model"))
    ai_base_url: str = Field(default="", validation_alias=AliasChoices("AI_BASE_URL", "ai_base_url"))
    ai_timeout_seconds: float = 45
    ai_max_upload_bytes: int = 5 * 1024 * 1024
    ai_min_confidence: float = 0.5
    frontend_url: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("FRONTEND_URL", "frontend_url"),
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    backend_host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("BACKEND_HOST", "backend_host"))
    training_data_dir: str = ""

    @field_validator("ai_api_key", mode="before")
    @classmethod
    def normalize_ai_api_key(cls, value: object) -> str:
        if value is None:
            return ""
        text = str(value).strip().strip('"').strip("'")
        return text

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_api_key)

    @property
    def ai_provider_name(self) -> str:
        return "Gemini"

    @property
    def uses_gemini(self) -> bool:
        name = str(getattr(self, "ai_provider", "Gemini") or "Gemini").strip().lower()
        return name in {"", "gemini", "google", "google-gemini", "google_genai"}

    @property
    def cors_origin_list(self) -> list[str]:
        origins: list[str] = []
        for origin in self.cors_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if not cleaned or cleaned == "*":
                continue
            if self.is_production and cleaned in _LOCAL_DEV_ORIGINS:
                continue
            if cleaned not in origins:
                origins.append(cleaned)
        frontend = self.frontend_url.strip().rstrip("/")
        if frontend and frontend != "*":
            if self.is_production and frontend in _LOCAL_DEV_ORIGINS:
                frontend = ""
            elif frontend not in origins:
                origins.insert(0, frontend)
        if not self.is_production:
            for local in ("http://localhost:5173", "http://127.0.0.1:5173"):
                if local not in origins:
                    origins.append(local)
        return origins

    @property
    def on_railway(self) -> bool:
        return bool(getattr(self, "railway_environment", "") or getattr(self, "railway_project_id", ""))

    @property
    def is_production(self) -> bool:
        if str(getattr(self, "environment", "") or "").lower() == "production":
            return True
        return str(getattr(self, "railway_environment", "") or "").lower() == "production"

    @property
    def requires_remote_database(self) -> bool:
        return self.is_production or self.on_railway

    @property
    def resolved_database_url(self) -> str:
        raw = str(getattr(self, "database_url", "") or "").strip()
        if self.requires_remote_database:
            if is_unconfigured_database_url(raw):
                raise RuntimeError("DATABASE_URL is not configured")
            return raw
        return raw or _DEV_DATABASE_URL

    @property
    def is_test(self) -> bool:
        return self.environment.lower() == "test"

    @property
    def refresh_cookie_secure(self) -> bool:
        return self.cookie_secure or self.is_production

    @property
    def refresh_cookie_samesite(self) -> str:
        value = self.cookie_samesite.lower().strip()
        if self.is_production and value == "lax":
            return "none"
        return value

    def resolved_training_data_dir(self):
        from pathlib import Path

        if self.training_data_dir:
            return Path(self.training_data_dir)
        return Path(__file__).resolve().parents[3] / "training" / "data"


def validate_production_settings(settings: Settings) -> None:
    if settings.requires_remote_database:
        raw = str(getattr(settings, "database_url", "") or "").strip()
        if is_unconfigured_database_url(raw):
            raise RuntimeError("DATABASE_URL is not configured")
        if "sqlite" in raw.lower():
            raise RuntimeError("SQLite is not allowed in production")
    if not settings.is_production:
        return
    secret = settings.jwt_secret_key.strip()
    if not secret or secret == _DEV_JWT_SECRET:
        raise RuntimeError("JWT_SECRET_KEY must be a unique secret in production")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
    if not settings.uses_gemini:
        raise RuntimeError("AI_PROVIDER must be Gemini")
    if not settings.cors_origin_list:
        raise RuntimeError("FRONTEND_URL must be set to the deployed frontend origin in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
