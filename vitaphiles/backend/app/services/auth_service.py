from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.models import Profile, RefreshToken, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, TokenResponse
from app.schemas.user import UserCreate, UserPublic, UserUpdate


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    def register(
        self,
        payload: UserCreate,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenResponse, str]:
        if self.users.get_by_email(payload.email) is not None:
            raise AppError("DUPLICATE_EMAIL", "An account with this email already exists", 409)
        if self.users.get_by_username(payload.username) is not None:
            raise AppError("DUPLICATE_USERNAME", "That username is taken", 409)
        try:
            user = self.users.create(
                email=payload.email,
                username=payload.username,
                password_hash=hash_password(payload.password),
            )
            self.db.flush()
            self.db.add(Profile(user_id=user.id, display_name=payload.display_name))
            raw = self._issue_refresh(user, ip_address=ip_address, user_agent=user_agent)
            self.db.commit()
            user = self.users.get_by_id(user.id) or user
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_EMAIL", "An account with this email or username already exists", 409) from exc
        return self._token_response(user), raw

    def login(
        self,
        email: str,
        password: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[TokenResponse, str]:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        if not user.is_active:
            raise AppError("UNAUTHORIZED", "Account is disabled", 401)
        raw = self._issue_refresh(user, ip_address=ip_address, user_agent=user_agent)
        self.db.commit()
        return self._token_response(user), raw

    def refresh(self, raw_token: str, *, ip_address: str | None, user_agent: str | None) -> tuple[TokenResponse, str]:
        token_hash = hash_refresh_token(raw_token)
        row = self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row is None:
            raise AppError("UNAUTHORIZED", "Invalid or expired session", 401)
        if row.revoked_at is not None:
            self._revoke_all(row.user_id, now)
            self.db.commit()
            raise AppError("UNAUTHORIZED", "Invalid or expired session", 401)
        if row.expires_at <= now:
            row.revoked_at = now
            self.db.commit()
            raise AppError("UNAUTHORIZED", "Invalid or expired session", 401)
        user = self.users.get_by_id(row.user_id)
        if user is None or not user.is_active:
            raise AppError("UNAUTHORIZED", "Invalid or expired session", 401)
        new_raw = new_refresh_token()
        replacement = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_raw),
            expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
            created_at=now,
            user_agent=(user_agent or "")[:512] or None,
            ip_address=(ip_address or "")[:64] or None,
        )
        self.db.add(replacement)
        self.db.flush()
        row.revoked_at = now
        row.replaced_by = replacement.id
        self.db.commit()
        user = self.users.get_by_id(user.id) or user
        return self._token_response(user), new_raw

    def logout(self, user: User | None, raw_refresh: str | None) -> User | None:
        now = datetime.now(timezone.utc)
        resolved = user
        if raw_refresh:
            token_hash = hash_refresh_token(raw_refresh)
            row = self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).scalar_one_or_none()
            if row is not None:
                resolved = self.users.get_by_id(row.user_id) or resolved
        if resolved is None:
            return None
        resolved.token_version = (resolved.token_version or 0) + 1
        self._revoke_all(resolved.id, now)
        self.db.commit()
        return resolved

    def get_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise AppError("UNAUTHORIZED", "Not authenticated", 401)
        return user

    def update_profile(self, user: User, payload: UserUpdate) -> User:
        profile = user.profile
        if profile is None:
            profile = Profile(user_id=user.id, display_name=user.username)
            self.db.add(profile)
            user.profile = profile
        if payload.display_name is not None:
            profile.display_name = payload.display_name
        if payload.bio is not None:
            profile.bio = payload.bio
        self.db.commit()
        return self.users.get_by_id(user.id) or user

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Current password is incorrect", 401)
        user.password_hash = hash_password(payload.new_password)
        user.token_version = (user.token_version or 0) + 1
        self._revoke_all(user.id, datetime.now(timezone.utc))
        self.db.commit()

    def _issue_refresh(self, user: User, *, ip_address: str | None, user_agent: str | None) -> str:
        now = datetime.now(timezone.utc)
        raw = new_refresh_token()
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(raw),
                expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
                created_at=now,
                user_agent=(user_agent or "")[:512] or None,
                ip_address=(ip_address or "")[:64] or None,
            )
        )
        return raw

    def _revoke_all(self, user_id: int, now: datetime) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    def _token_response(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id=user.id, token_version=user.token_version or 0),
            user=to_user_public(user),
        )


def to_user_public(user: User) -> UserPublic:
    profile = user.profile
    return UserPublic(
        id=user.id,
        email=user.email,
        username=user.username,
        display_name=profile.display_name if profile else user.username,
        bio=profile.bio if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        created_at=user.created_at,
    )
