from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Movie(TimestampMixin, Base):
    __tablename__ = "movies"
    __table_args__ = (UniqueConstraint("external_source", "external_id", name="uq_movies_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(400), nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    backdrop_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    released_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    external_source: Mapped[str] = mapped_column(String(40), nullable=False, default="tmdb")
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0, server_default="0")
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    credits: Mapped[list["MovieCredit"]] = relationship("MovieCredit", back_populates="movie", cascade="all, delete-orphan")
