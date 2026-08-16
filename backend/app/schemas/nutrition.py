from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.enums import MealType
from app.utils.pagination import PaginatedResponse


class DecimalJsonModel(BaseModel):
    @field_serializer("*", when_used="json")
    def serialize_decimals(self, value: object) -> object:
        return float(value) if isinstance(value, Decimal) else value


class MacroSnapshot(DecimalJsonModel):
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal = Decimal("0")
    sugar: Decimal = Decimal("0")


class RemainingMacros(DecimalJsonModel):
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal


class GoalTargets(DecimalJsonModel):
    daily_calorie_target: Decimal
    protein_target: Decimal
    carb_target: Decimal
    fat_target: Decimal


class DailyMealSummary(DecimalJsonModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_type: MealType
    consumed_at: datetime
    notes: str | None
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    food_count: int


class RecentFood(DecimalJsonModel):
    food_name: str
    quantity: Decimal
    unit: str
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    consumed_at: datetime
    meal_id: int
    meal_type: MealType


class DailyNutritionResponse(DecimalJsonModel):
    date: date
    totals: MacroSnapshot
    remaining: RemainingMacros | None
    goals: GoalTargets | None
    meals: list[DailyMealSummary]
    recent_foods: list[RecentFood]


class DayPoint(DecimalJsonModel):
    date: date
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal


class WeeklyNutritionResponse(DecimalJsonModel):
    start_date: date
    end_date: date
    totals: MacroSnapshot
    days: list[DayPoint]


class TrendListResponse(PaginatedResponse[DayPoint]):
    start_date: date
    end_date: date
    totals: MacroSnapshot


class MicronutrientTotal(DecimalJsonModel):
    nutrient_name: str
    amount: Decimal
    unit: str


class MicronutrientListResponse(PaginatedResponse[MicronutrientTotal]):
    start_date: date
    end_date: date


class GoalComparisonItem(DecimalJsonModel):
    name: str
    label: str
    unit: str
    actual: Decimal
    target: Decimal | None
    remaining: Decimal | None
    percent: Decimal


class GoalComparisonResponse(DecimalJsonModel):
    date: date
    start_date: date
    end_date: date
    days: int
    has_goals: bool
    items: list[GoalComparisonItem]
