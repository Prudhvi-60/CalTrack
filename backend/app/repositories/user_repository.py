from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, *, email: str, name: str, password_hash: str) -> User:
        user = User(email=email.lower(), name=name, password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
