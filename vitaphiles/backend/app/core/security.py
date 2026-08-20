from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

_BCRYPT_MAX_BYTES = 72
REFRESH_COOKIE_NAME = "vitaphiles_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    token_version: int


def hash_password(password: str) -> str:
    digest = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(digest, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    digest = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(digest, password_hash.encode("utf-8"))


def hash_refresh_token(raw_token: str) -> str:
    pepper = get_settings().jwt_refresh_secret
    material = f"{pepper}:{raw_token}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(*, user_id: int, token_version: int) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "type": "access",
        "ver": token_version,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> AccessClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token")
    try:
        user_id = int(payload.get("user_id") or payload.get("sub"))
        token_version = int(payload.get("ver", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid token") from exc
    return AccessClaims(user_id=user_id, token_version=token_version)
