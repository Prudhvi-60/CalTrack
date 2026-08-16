from datetime import datetime, timedelta, timezone

from fastapi import Response

from app.core.config import Settings
from app.core.security import REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH


def set_refresh_cookie(response: Response, raw_token: str, settings: Settings) -> None:
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    secure = settings.refresh_cookie_secure
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=max_age,
        expires=datetime.now(timezone.utc) + timedelta(seconds=max_age),
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite=settings.refresh_cookie_samesite,  # type: ignore[arg-type]
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    secure = settings.refresh_cookie_secure
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite=settings.refresh_cookie_samesite,  # type: ignore[arg-type]
    )
