from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import GenreKind
from app.models.mixins import TimestampMixin


class Genre(TimestampMixin, Base):
    __tablename__ = "genres"
    __table_args__ = (UniqueConstraint("slug", name="uq_genres_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default=GenreKind.BOTH.value)
