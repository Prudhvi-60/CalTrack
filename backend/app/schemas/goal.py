from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.utils.pagination import PaginatedResponse

_ZERO = Decimal("0")


class GoalCreate(BaseModel):
    daily_calorie_target: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    protein_target: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    carb_target: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    fat_target: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    weight_goal: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)


class GoalUpdate(GoalCreate):
    """Full replacement of the current user's goals."""


class GoalPatch(BaseModel):
    daily_calorie_target: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    protein_target: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    carb_target: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    fat_target: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    weight_goal: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)


class GoalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    daily_calorie_target: Decimal
    protein_target: Decimal
    carb_target: Decimal
    fat_target: Decimal
    weight_goal: Decimal | None
    calories_actual: Decimal = _ZERO
    protein_actual: Decimal = _ZERO
    carb_actual: Decimal = _ZERO
    fat_actual: Decimal = _ZERO
    calories_remaining: Decimal = _ZERO
    protein_remaining: Decimal = _ZERO
    carb_remaining: Decimal = _ZERO
    fat_remaining: Decimal = _ZERO
    progress_date: date
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "daily_calorie_target",
        "protein_target",
        "carb_target",
        "fat_target",
        "weight_goal",
        "calories_actual",
        "protein_actual",
        "carb_actual",
        "fat_actual",
        "calories_remaining",
        "protein_remaining",
        "carb_remaining",
        "fat_remaining",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return None if value is None else float(value)


GoalListResponse = PaginatedResponse[GoalPublic]
