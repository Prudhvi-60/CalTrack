from datetime import date as Date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import MealType
from app.schemas.meal import MealPublic

NutritionStatus = Literal["matched", "unknown"]
MealSlot = Literal["breakfast", "morning_snack", "lunch", "evening_snack", "dinner", "other"]


class MealPlanFood(BaseModel):
    food: str = Field(min_length=1, max_length=255)
    quantity: Decimal | None = None
    quantity_text: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=40)
    notes: str = ""
    original_label: str | None = Field(default=None, max_length=80)
    meal_name: str | None = Field(default=None, max_length=255)
    alternative: str | None = Field(default=None, max_length=255)
    nutrition_status: NutritionStatus = "unknown"
    matched_food: str | None = None
    calories: Decimal | None = None
    protein: Decimal | None = None
    carbohydrates: Decimal | None = None
    fat: Decimal | None = None
    fiber: Decimal | None = None
    sugar: Decimal | None = None

    @field_validator("food")
    @classmethod
    def strip_food(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("food is required")
        return text[:255]


class MealPlanMeals(BaseModel):
    breakfast: list[MealPlanFood] = Field(default_factory=list)
    morning_snack: list[MealPlanFood] = Field(default_factory=list)
    lunch: list[MealPlanFood] = Field(default_factory=list)
    evening_snack: list[MealPlanFood] = Field(default_factory=list)
    dinner: list[MealPlanFood] = Field(default_factory=list)
    other: list[MealPlanFood] = Field(default_factory=list)


class MealPlanDay(BaseModel):
    day: int | None = Field(default=None, ge=1, le=366)
    date: Date | None = None
    label: str | None = Field(default=None, max_length=80)
    meals: MealPlanMeals = Field(default_factory=MealPlanMeals)


class MealPlanPreviewResponse(BaseModel):
    success: bool = True
    document_type: str = "meal_plan"
    title: str | None = None
    extraction_method: str = "text"
    days_detected: int = 0
    meals_detected: int = 0
    foods_detected: int = 0
    warnings: list[str] = Field(default_factory=list)
    days: list[MealPlanDay] = Field(default_factory=list)


class MealPlanConfirmFood(BaseModel):
    food: str = Field(min_length=1, max_length=255)
    quantity: Decimal | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=40)
    notes: str = ""
    original_label: str | None = None
    meal_name: str | None = None
    alternative: str | None = None
    nutrition_status: NutritionStatus = "unknown"
    calories: Decimal | None = Field(default=None, ge=0)
    protein: Decimal | None = Field(default=None, ge=0)
    carbohydrates: Decimal | None = Field(default=None, ge=0)
    fat: Decimal | None = Field(default=None, ge=0)
    fiber: Decimal | None = Field(default=None, ge=0)
    sugar: Decimal | None = Field(default=None, ge=0)
    slot: MealSlot
    include: bool = True


class MealPlanConfirmDay(BaseModel):
    day: int | None = Field(default=None, ge=1, le=366)
    date: Date
    label: str | None = None
    foods: list[MealPlanConfirmFood] = Field(min_length=1, max_length=80)
    include: bool = True


class MealPlanConfirmRequest(BaseModel):
    days: list[MealPlanConfirmDay] = Field(min_length=1, max_length=62)


class MealPlanConfirmResponse(BaseModel):
    imported_meals: int
    imported_foods: int
    meals: list[MealPublic]
    meal_types: list[MealType] = Field(default_factory=list)
