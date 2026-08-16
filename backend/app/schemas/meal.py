from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.models.enums import MealType, NutrientName
from app.utils.pagination import PaginatedResponse
from app.utils.validators import ensure_utc

DecFloat = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
MicroAmount = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=4)]


class DecimalJsonModel(BaseModel):
    @field_serializer("*", when_used="json")
    def serialize_decimals(self, value: object) -> object:
        return float(value) if isinstance(value, Decimal) else value


class MicronutrientCreate(BaseModel):
    nutrient_name: NutrientName
    amount: MicroAmount
    unit: str = Field(min_length=1, max_length=20)


class MicronutrientPublic(DecimalJsonModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nutrient_name: str
    amount: Decimal
    unit: str


class FoodEntryCreate(BaseModel):
    food_name: str = Field(min_length=1, max_length=255)
    quantity: DecFloat
    unit: str = Field(min_length=1, max_length=40)
    calories: DecFloat
    protein: DecFloat
    carbohydrates: DecFloat
    fat: DecFloat
    fiber: DecFloat = Decimal("0")
    sugar: DecFloat = Decimal("0")
    micronutrients: list[MicronutrientCreate] = Field(default_factory=list)


class FoodEntryPublic(DecimalJsonModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    food_name: str
    quantity: Decimal
    unit: str
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal
    sugar: Decimal
    micronutrients: list[MicronutrientPublic]


class MealCreate(BaseModel):
    meal_type: MealType
    consumed_at: datetime
    notes: str | None = Field(default=None, max_length=2000)
    food_entries: list[FoodEntryCreate] = Field(min_length=1)

    @field_validator("consumed_at")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("notes")
    @classmethod
    def empty_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class MealUpdate(MealCreate):
    """Full replacement of a meal and its food entries."""


class MealTotals(DecimalJsonModel):
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal
    sugar: Decimal


class MealPublic(DecimalJsonModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    meal_type: MealType
    consumed_at: datetime
    notes: str | None
    food_entries: list[FoodEntryPublic]
    totals: MealTotals
    created_at: datetime
    updated_at: datetime


MealListResponse = PaginatedResponse[MealPublic]
