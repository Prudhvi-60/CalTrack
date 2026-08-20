from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Book(TimestampMixin, Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("external_source", "external_id", name="uq_books_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    subtitle: Mapped[str | None] = mapped_column(String(400), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    isbn10: Mapped[str | None] = mapped_column(String(16), nullable=True)
    isbn13: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    cover_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    published_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    external_source: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0, server_default="0")
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    authors: Mapped[list["BookAuthor"]] = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
