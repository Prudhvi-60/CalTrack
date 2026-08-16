from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MealType
from app.models.mixins import TimestampMixin


class Meal(TimestampMixin, Base):
    __tablename__ = "meals"
    __table_args__ = (
        Index("ix_meals_user_id_consumed_at", "user_id", "consumed_at"),
        Index("ix_meals_user_id_meal_type", "user_id", "meal_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meal_type: Mapped[MealType] = mapped_column(
        Enum(MealType, name="meal_type", native_enum=True),
        nullable=False,
    )
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="meals")
    food_entries: Mapped[list["FoodEntry"]] = relationship(
        "FoodEntry",
        back_populates="meal",
        cascade="all, delete-orphan",
    )
