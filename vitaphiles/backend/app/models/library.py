from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReadingStatus
from app.models.mixins import TimestampMixin

_RATING = (
    "rating IS NULL OR (rating >= 0.5 AND rating <= 5 AND (rating * 2) = trunc(rating * 2))"
)


class UserBook(TimestampMixin, Base):
    __tablename__ = "user_books"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_books"),
        CheckConstraint(_RATING, name="ck_user_books_rating"),
        CheckConstraint("progress_pages IS NULL OR progress_pages >= 0", name="ck_user_books_progress"),
        Index("ix_user_books_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ReadingStatus.WANT_TO_READ.value)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)

    user: Mapped["User"] = relationship("User")
    book: Mapped["Book"] = relationship("Book")


class UserMovie(TimestampMixin, Base):
    __tablename__ = "user_movies"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movies"),
        CheckConstraint(_RATING, name="ck_user_movies_rating"),
        CheckConstraint("rewatch_count >= 0", name="ck_user_movies_rewatch"),
        Index("ix_user_movies_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    watched_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    rewatch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    user: Mapped["User"] = relationship("User")
    movie: Mapped["Movie"] = relationship("Movie")
