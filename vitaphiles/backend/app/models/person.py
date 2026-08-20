from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Person(TimestampMixin, Base):
    __tablename__ = "people"
    __table_args__ = (UniqueConstraint("tmdb_id", name="uq_people_tmdb_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
