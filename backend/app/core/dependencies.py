from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("UNAUTHORIZED", "Not authenticated", 401)
    try:
        claims = decode_access_token(credentials.credentials)
    except (ValueError, TypeError) as exc:
        raise AppError("UNAUTHORIZED", "Invalid or expired token", 401) from exc
    user = AuthService(db).get_user(claims.user_id)
    if (user.token_version or 0) != claims.token_version:
        raise AppError("UNAUTHORIZED", "Invalid or expired token", 401)
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        claims = decode_access_token(credentials.credentials)
        user = AuthService(db).get_user(claims.user_id)
    except AppError:
        return None
    except (ValueError, TypeError):
        return None
    if (user.token_version or 0) != claims.token_version:
        return None
    return user


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host
    return None
