from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ItemKind
from app.models.mixins import TimestampMixin


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint(
            "(item_kind = 'BOOK' AND book_id IS NOT NULL AND movie_id IS NULL) OR "
            "(item_kind = 'MOVIE' AND movie_id IS NOT NULL AND book_id IS NULL)",
            name="ck_reviews_item",
        ),
        CheckConstraint(
            "rating >= 0.5 AND rating <= 5 AND (rating * 2) = trunc(rating * 2)",
            name="ck_reviews_rating",
        ),
        Index(
            "uq_reviews_user_book",
            "user_id",
            "book_id",
            unique=True,
            postgresql_where=text("book_id IS NOT NULL"),
        ),
        Index(
            "uq_reviews_user_movie",
            "user_id",
            "movie_id",
            unique=True,
            postgresql_where=text("movie_id IS NOT NULL"),
        ),
        Index("ix_reviews_book_created", "book_id", "created_at"),
        Index("ix_reviews_movie_created", "movie_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_kind: Mapped[str] = mapped_column(nullable=False, default=ItemKind.BOOK.value)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=True)
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    is_spoiler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    user: Mapped["User"] = relationship("User")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="review", cascade="all, delete-orphan")


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    review: Mapped["Review"] = relationship("Review", back_populates="comments")


class Like(TimestampMixin, Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="uq_likes_user_review"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
