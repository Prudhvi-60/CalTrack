from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.exceptions import AppError
from app.models import User
from app.models.enums import MealType
from app.schemas.meal import FoodEntryCreate, MealCreate
from app.services.goal_service import GoalService
from app.services.meal_service import MealService
from app.services.nutrition_service import NutritionService
from sqlalchemy.orm import Session


class EmptyArgs(BaseModel):
    pass


class MealHistoryArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    on_date: date | None = Field(default=None, alias="date")
    start_date: date | None = None
    end_date: date | None = None
    meal_type: MealType | None = None
    q: str | None = Field(default=None, max_length=120)
    page: int = Field(default=1, ge=1, le=50)


class CreateMealArgs(MealCreate):
    pass


class AddFoodArgs(FoodEntryCreate):
    meal_id: int | None = Field(default=None, ge=1)
    meal_type: MealType | None = None
    consumed_at: datetime | None = None


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_today_nutrition",
            "description": "Daily calorie and macro totals, remaining budget, and today's meals.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_summary",
            "description": "Last 7 days of calorie and macro totals.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": "Current user's calorie and macro targets.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_meal_history",
            "description": "List the current user's meals with optional date and type filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "meal_type": {"type": "string", "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"]},
                    "q": {"type": "string"},
                    "page": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_meal",
            "description": "Create a meal with one or more food entries for the current user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meal_type": {"type": "string", "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"]},
                    "consumed_at": {"type": "string", "description": "ISO-8601 datetime"},
                    "notes": {"type": "string"},
                    "food_entries": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
                "required": ["meal_type", "consumed_at", "food_entries"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_food_entry",
            "description": "Add a food to an existing meal, or to today's meal of the given type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meal_id": {"type": "integer"},
                    "meal_type": {"type": "string", "enum": ["BREAKFAST", "LUNCH", "DINNER", "SNACK"]},
                    "consumed_at": {"type": "string"},
                    "food_name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "calories": {"type": "number"},
                    "protein": {"type": "number"},
                    "carbohydrates": {"type": "number"},
                    "fat": {"type": "number"},
                    "fiber": {"type": "number"},
                    "sugar": {"type": "number"},
                },
                "required": ["food_name", "quantity", "unit", "calories", "protein", "carbohydrates", "fat"],
            },
        },
    },
]


class ChatToolbox:
    def __init__(self, db: Session, user: User) -> None:
        self.user = user
        self.nutrition = NutritionService(db, user)
        self.meals = MealService(db, user)
        self.goals = GoalService(db, user)

    def execute(self, name: str, raw_args: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
        handlers: dict[str, tuple[type[BaseModel], Callable[[BaseModel], object]]] = {
            "get_today_nutrition": (EmptyArgs, lambda _: self.nutrition.daily(None)),
            "get_weekly_summary": (EmptyArgs, lambda _: self.nutrition.weekly(None)),
            "get_goals": (EmptyArgs, self._goals),
            "get_meal_history": (MealHistoryArgs, self._history),
            "create_meal": (CreateMealArgs, lambda args: self.meals.create(args)),  # type: ignore[arg-type]
            "add_food_entry": (AddFoodArgs, self._add_food),
        }
        if name not in handlers:
            return False, {"error": "Unknown tool"}, f"Unknown tool {name}"
        schema, handler = handlers[name]
        try:
            parsed = schema.model_validate(raw_args or {})
            result = handler(parsed)
        except ValidationError as exc:
            return False, {"error": exc.errors()}, "Tool arguments failed validation"
        except AppError as exc:
            return False, {"error": {"code": exc.code, "message": exc.message}}, exc.message
        dumped = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        return True, dumped, _summary(name, dumped)

    def _goals(self, _: EmptyArgs) -> object:
        listing = self.goals.list_goals(page=1, page_size=1)
        if listing.total == 0:
            return listing
        return listing.items[0]

    def _history(self, args: MealHistoryArgs) -> object:
        return self.meals.list_meals(
            page=args.page,
            page_size=10,
            meal_type=args.meal_type,
            on_date=args.on_date,
            start_date=args.start_date,
            end_date=args.end_date,
            search=args.q,
        )

    def _add_food(self, args: AddFoodArgs) -> object:
        food = FoodEntryCreate(
            food_name=args.food_name,
            quantity=args.quantity,
            unit=args.unit,
            calories=args.calories,
            protein=args.protein,
            carbohydrates=args.carbohydrates,
            fat=args.fat,
            fiber=args.fiber,
            sugar=args.sugar,
            micronutrients=args.micronutrients,
        )
        if args.meal_id is not None:
            return self.meals.add_food(args.meal_id, food)
        meal_type = args.meal_type or MealType.SNACK
        day = (args.consumed_at or datetime.now(timezone.utc)).date()
        existing = self.meals.list_meals(
            page=1,
            page_size=1,
            meal_type=meal_type,
            on_date=day,
            start_date=None,
            end_date=None,
            search=None,
        )
        if existing.items:
            return self.meals.add_food(existing.items[0].id, food)
        consumed_at = args.consumed_at or datetime.now(timezone.utc)
        return self.meals.create(
            MealCreate(meal_type=meal_type, consumed_at=consumed_at, notes=None, food_entries=[food])
        )


def _summary(name: str, dumped: object) -> str:
    if isinstance(dumped, dict) and "totals" in dumped:
        totals = dumped["totals"]
        if isinstance(totals, dict) and "calories" in totals:
            return f"{name}: {totals['calories']} kcal"
    if isinstance(dumped, dict) and "id" in dumped:
        return f"{name}: saved meal {dumped['id']}"
    if isinstance(dumped, dict) and "total" in dumped:
        return f"{name}: {dumped['total']} meals"
    return f"{name}: ok"
