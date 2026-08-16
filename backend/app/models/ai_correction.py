from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AiCorrection(TimestampMixin, Base):
    __tablename__ = "ai_corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    predicted_name: Mapped[str] = mapped_column(String(255), nullable=False)
    predicted_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    predicted_unit: Mapped[str] = mapped_column(String(40), nullable=False)
    corrected_name: Mapped[str] = mapped_column(String(255), nullable=False)
    corrected_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    corrected_unit: Mapped[str] = mapped_column(String(40), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(20), nullable=False, default="food")

    user: Mapped["User"] = relationship("User", back_populates="ai_corrections")
