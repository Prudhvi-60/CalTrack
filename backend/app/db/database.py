from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.database_url import engine_kwargs, sqlalchemy_database_url

settings = get_settings()
_url = sqlalchemy_database_url(settings.resolved_database_url)

engine = create_engine(
    _url,
    **engine_kwargs(
        _url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
    ),
)
