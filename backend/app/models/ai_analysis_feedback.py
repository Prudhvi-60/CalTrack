from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AiAnalysisFeedback(TimestampMixin, Base):
    __tablename__ = "ai_analysis_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    image_reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    predicted_food: Mapped[str] = mapped_column(String(255), nullable=False)
    corrected_food: Mapped[str] = mapped_column(String(255), nullable=False)
    predicted_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    corrected_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    predicted_unit: Mapped[str] = mapped_column(String(40), nullable=False)
    corrected_unit: Mapped[str] = mapped_column(String(40), nullable=False)
    predicted_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    include_in_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="ai_analysis_feedback")
    analysis: Mapped["AiAnalysis | None"] = relationship("AiAnalysis", back_populates="feedback")
