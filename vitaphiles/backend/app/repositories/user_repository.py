from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.execute(
            select(User).options(joinedload(User.profile)).where(User.id == user_id)
        ).unique().scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User)
            .options(joinedload(User.profile))
            .where(func.lower(User.email) == email.lower())
        ).unique().scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        return self.db.execute(
            select(User)
            .options(joinedload(User.profile))
            .where(func.lower(User.username) == username.lower())
        ).unique().scalar_one_or_none()

    def create(self, *, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        return user
