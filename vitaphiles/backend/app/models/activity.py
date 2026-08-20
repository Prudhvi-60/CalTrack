from sqlalchemy import Boolean, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import ActivityVerb
from app.models.mixins import TimestampMixin


class Activity(TimestampMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (Index("ix_activities_actor_created", "actor_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    verb: Mapped[str] = mapped_column(String(40), nullable=False, default=ActivityVerb.BOOK_ADDED.value, index=True)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="SET NULL"), nullable=True)
    review_id: Mapped[int | None] = mapped_column(ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
    list_id: Mapped[int | None] = mapped_column(ForeignKey("lists.id", ondelete="SET NULL"), nullable=True)
    followee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    payload: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )

    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    payload: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=dict,
        server_default=text("'{}'"),
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
