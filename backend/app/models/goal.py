from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Goal(TimestampMixin, Base):
    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_goals_user_id"),
        CheckConstraint("daily_calorie_target >= 0", name="ck_goals_calories_non_negative"),
        CheckConstraint("protein_target >= 0", name="ck_goals_protein_non_negative"),
        CheckConstraint("carb_target >= 0", name="ck_goals_carb_non_negative"),
        CheckConstraint("fat_target >= 0", name="ck_goals_fat_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    daily_calorie_target: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    protein_target: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    carb_target: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fat_target: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    weight_goal: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="goals")
