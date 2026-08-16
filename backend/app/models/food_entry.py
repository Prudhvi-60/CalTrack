from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class FoodEntry(TimestampMixin, Base):
    __tablename__ = "food_entries"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_food_entries_quantity_non_negative"),
        CheckConstraint("calories >= 0", name="ck_food_entries_calories_non_negative"),
        CheckConstraint("protein >= 0", name="ck_food_entries_protein_non_negative"),
        CheckConstraint("carbohydrates >= 0", name="ck_food_entries_carbohydrates_non_negative"),
        CheckConstraint("fat >= 0", name="ck_food_entries_fat_non_negative"),
        CheckConstraint("fiber >= 0", name="ck_food_entries_fiber_non_negative"),
        CheckConstraint("sugar >= 0", name="ck_food_entries_sugar_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_id: Mapped[int] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    calories: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    protein: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    carbohydrates: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fat: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fiber: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    sugar: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    meal: Mapped["Meal"] = relationship("Meal", back_populates="food_entries")
    micronutrients: Mapped[list["Micronutrient"]] = relationship(
        "Micronutrient",
        back_populates="food_entry",
        cascade="all, delete-orphan",
    )
