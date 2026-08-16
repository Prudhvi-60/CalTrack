from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    allow_training_data_collection: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    meals: Mapped[list["Meal"]] = relationship(
        "Meal",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_corrections: Mapped[list["AiCorrection"]] = relationship(
        "AiCorrection",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="RefreshToken.user_id",
    )
    ai_analyses: Mapped[list["AiAnalysis"]] = relationship(
        "AiAnalysis",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_analysis_feedback: Mapped[list["AiAnalysisFeedback"]] = relationship(
        "AiAnalysisFeedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )
