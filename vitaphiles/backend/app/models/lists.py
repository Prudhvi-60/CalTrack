from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ItemKind, ListPrivacy
from app.models.mixins import TimestampMixin


class UserList(TimestampMixin, Base):
    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    privacy: Mapped[str] = mapped_column(String(24), nullable=False, default=ListPrivacy.PUBLIC.value)

    owner: Mapped["User"] = relationship("User")
    items: Mapped[list["ListItem"]] = relationship(
        "ListItem",
        back_populates="list",
        cascade="all, delete-orphan",
        order_by="ListItem.position",
    )


class ListItem(TimestampMixin, Base):
    __tablename__ = "list_items"
    __table_args__ = (
        CheckConstraint(
            "(item_kind = 'BOOK' AND book_id IS NOT NULL AND movie_id IS NULL) OR "
            "(item_kind = 'MOVIE' AND movie_id IS NOT NULL AND book_id IS NULL)",
            name="ck_list_items_item",
        ),
        Index(
            "uq_list_items_book",
            "list_id",
            "book_id",
            unique=True,
            postgresql_where=text("book_id IS NOT NULL"),
        ),
        Index(
            "uq_list_items_movie",
            "list_id",
            "movie_id",
            unique=True,
            postgresql_where=text("movie_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("lists.id", ondelete="CASCADE"), nullable=False, index=True)
    item_kind: Mapped[str] = mapped_column(String(16), nullable=False, default=ItemKind.BOOK.value)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=True)
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    list: Mapped[UserList] = relationship("UserList", back_populates="items")
