from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Micronutrient(TimestampMixin, Base):
    __tablename__ = "micronutrients"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_micronutrients_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    food_entry_id: Mapped[int] = mapped_column(
        ForeignKey("food_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nutrient_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    food_entry: Mapped["FoodEntry"] = relationship("FoodEntry", back_populates="micronutrients")
