from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_name: str = "Vitaphiles API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+psycopg://vitaphiles:vitaphiles@localhost:5433/vitaphiles",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    jwt_secret_key: str = Field(
        default="change-me-to-a-long-random-secret-min-32-chars",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "JWT_SECRET"),
    )
    jwt_refresh_secret: str = Field(
        default="change-me-refresh-secret-min-32-chars-too",
        validation_alias=AliasChoices("JWT_REFRESH_SECRET", "jwt_refresh_secret"),
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    frontend_url: str = "http://localhost:5174"
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"
    tmdb_api_key: str = Field(default="", validation_alias=AliasChoices("TMDB_API_KEY"))
    google_books_api_key: str = Field(default="", validation_alias=AliasChoices("GOOGLE_BOOKS_API_KEY"))

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]
        front = self.frontend_url.strip().rstrip("/")
        if front and front not in origins:
            origins.insert(0, front)
        return origins

    @property
    def resolved_database_url(self) -> str:
        raw = self.database_url.strip()
        if raw.startswith("postgres://"):
            raw = "postgresql://" + raw[len("postgres://") :]
        if raw.startswith("postgresql://") and "+psycopg" not in raw:
            raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
        return raw


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
