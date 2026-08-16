from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database_url import sqlalchemy_database_url
from app.db.base import Base
from app.models import (  # noqa: F401
    AiAnalysis,
    AiAnalysisFeedback,
    AiCorrection,
    FoodEntry,
    Goal,
    Meal,
    Micronutrient,
    RefreshToken,
    User,
)

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", sqlalchemy_database_url(settings.database_url).replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = sqlalchemy_database_url(settings.database_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
