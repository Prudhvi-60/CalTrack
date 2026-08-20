from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Author(TimestampMixin, Base):
    __tablename__ = "authors"
    __table_args__ = (UniqueConstraint("name", name="uq_authors_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
