from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Goal, Meal, User
from app.repositories.goal_repository import GoalRepository
from app.repositories.meal_repository import MealRepository
from app.schemas.nutrition import (
    DailyMealSummary,
    DailyNutritionResponse,
    DayPoint,
    GoalComparisonItem,
    GoalComparisonResponse,
    GoalTargets,
    MacroSnapshot,
    MicronutrientListResponse,
    MicronutrientTotal,
    RecentFood,
    RemainingMacros,
    TrendListResponse,
    WeeklyNutritionResponse,
)
from app.utils.nutrition import MacroTotals, percent_of_target, remaining, sum_food_macros, sum_micronutrients
from app.utils.pagination import paginated


class NutritionService:
    def __init__(self, db: Session, user: User) -> None:
        self.user = user
        self.meals = MealRepository(db)
        self.goals = GoalRepository(db)

    def daily(self, day: date | None) -> DailyNutritionResponse:
        target_day = day or _utc_today()
        meals = self.meals.list_in_range(self.user.id, target_day, target_day)
        entries = _flatten_entries(meals)
        totals = sum_food_macros(entries)
        goal = self.goals.get_for_user(self.user.id)
        recent = _recent_foods(meals, limit=8)
        return DailyNutritionResponse(
            date=target_day,
            totals=_snapshot(totals),
            remaining=_remaining_for(goal, totals),
            goals=_targets(goal),
            meals=[_meal_summary(meal) for meal in meals],
            recent_foods=recent,
        )

    def weekly(self, end_date: date | None) -> WeeklyNutritionResponse:
        end = end_date or _utc_today()
        start = end - timedelta(days=6)
        days = self._day_points(start, end)
        totals = _sum_points(days)
        return WeeklyNutritionResponse(start_date=start, end_date=end, totals=totals, days=days)

    def trends(self, days: int, page: int, page_size: int) -> TrendListResponse:
        if days not in {7, 30, 90}:
            raise AppError("VALIDATION_ERROR", "days must be 7, 30, or 90", 422)
        end = _utc_today()
        start = end - timedelta(days=days - 1)
        points = self._day_points(start, end)
        offset = (page - 1) * page_size
        page_items = points[offset : offset + page_size]
        result = paginated(page_items, total=len(points), page=page, page_size=page_size)
        return TrendListResponse(
            items=result.items,
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            total_pages=result.total_pages,
            start_date=start,
            end_date=end,
            totals=_sum_points(points),
        )

    def micronutrients(
        self,
        *,
        days: int | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> MicronutrientListResponse:
        start, end, _count = _resolve_window(days=days, start_date=start_date, end_date=end_date, day=None)
        meals = self.meals.list_in_range(self.user.id, start, end, include_micros=True)
        totals = [
            MicronutrientTotal(nutrient_name=item.nutrient_name, amount=item.amount, unit=item.unit)
            for item in sum_micronutrients(_flatten_entries(meals))
        ]
        offset = (page - 1) * page_size
        result = paginated(totals[offset : offset + page_size], total=len(totals), page=page, page_size=page_size)
        return MicronutrientListResponse(
            items=result.items,
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            total_pages=result.total_pages,
            start_date=start,
            end_date=end,
        )

    def goal_comparison(self, day: date | None, days: int | None) -> GoalComparisonResponse:
        start, end, count = _resolve_window(days=days, start_date=None, end_date=None, day=day)
        by_day = self.meals.macros_by_day(self.user.id, start, end)
        totals = MacroTotals()
        for day_totals in by_day.values():
            totals = MacroTotals(
                calories=totals.calories + day_totals.calories,
                protein=totals.protein + day_totals.protein,
                carbohydrates=totals.carbohydrates + day_totals.carbohydrates,
                fat=totals.fat + day_totals.fat,
                fiber=totals.fiber + day_totals.fiber,
                sugar=totals.sugar + day_totals.sugar,
            )
        goal = self.goals.get_for_user(self.user.id)
        scale = Decimal(count)
        items = [
            _comparison(
                "calories",
                "Calories",
                "kcal",
                totals.calories,
                goal.daily_calorie_target * scale if goal else None,
            ),
            _comparison(
                "protein",
                "Protein",
                "g",
                totals.protein,
                goal.protein_target * scale if goal else None,
            ),
            _comparison(
                "carbohydrates",
                "Carbohydrates",
                "g",
                totals.carbohydrates,
                goal.carb_target * scale if goal else None,
            ),
            _comparison(
                "fat",
                "Fat",
                "g",
                totals.fat,
                goal.fat_target * scale if goal else None,
            ),
        ]
        return GoalComparisonResponse(
            date=end,
            start_date=start,
            end_date=end,
            days=count,
            has_goals=goal is not None,
            items=items,
        )

    def _day_points(self, start: date, end: date) -> list[DayPoint]:
        by_day = self.meals.macros_by_day(self.user.id, start, end)
        points: list[DayPoint] = []
        cursor = start
        while cursor <= end:
            totals = by_day.get(cursor, MacroTotals())
            points.append(
                DayPoint(
                    date=cursor,
                    calories=totals.calories,
                    protein=totals.protein,
                    carbohydrates=totals.carbohydrates,
                    fat=totals.fat,
                )
            )
            cursor += timedelta(days=1)
        return points


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _resolve_window(
    *,
    days: int | None,
    start_date: date | None,
    end_date: date | None,
    day: date | None,
) -> tuple[date, date, int]:
    if days is not None:
        if days not in {7, 30, 90}:
            raise AppError("VALIDATION_ERROR", "days must be 7, 30, or 90", 422)
        end = _utc_today()
        start = end - timedelta(days=days - 1)
        return start, end, days
    if day is not None:
        return day, day, 1
    if start_date is not None or end_date is not None:
        end = end_date or _utc_today()
        start = start_date or end
        if start > end:
            raise AppError("VALIDATION_ERROR", "start_date must be on or before end_date", 422)
        return start, end, (end - start).days + 1
    today = _utc_today()
    return today, today, 1


def _flatten_entries(meals: list[Meal]):
    entries = []
    for meal in meals:
        entries.extend(meal.food_entries)
    return entries


def _snapshot(totals: MacroTotals) -> MacroSnapshot:
    return MacroSnapshot(
        calories=totals.calories,
        protein=totals.protein,
        carbohydrates=totals.carbohydrates,
        fat=totals.fat,
        fiber=totals.fiber,
        sugar=totals.sugar,
    )


def _targets(goal: Goal | None) -> GoalTargets | None:
    if goal is None:
        return None
    return GoalTargets(
        daily_calorie_target=goal.daily_calorie_target,
        protein_target=goal.protein_target,
        carb_target=goal.carb_target,
        fat_target=goal.fat_target,
    )


def _remaining_for(goal: Goal | None, totals: MacroTotals) -> RemainingMacros | None:
    if goal is None:
        return None
    return RemainingMacros(
        calories=remaining(goal.daily_calorie_target, totals.calories),
        protein=remaining(goal.protein_target, totals.protein),
        carbohydrates=remaining(goal.carb_target, totals.carbohydrates),
        fat=remaining(goal.fat_target, totals.fat),
    )


def _meal_summary(meal: Meal) -> DailyMealSummary:
    totals = sum_food_macros(meal.food_entries)
    return DailyMealSummary(
        id=meal.id,
        meal_type=meal.meal_type,
        consumed_at=meal.consumed_at,
        notes=meal.notes,
        calories=totals.calories,
        protein=totals.protein,
        carbohydrates=totals.carbohydrates,
        fat=totals.fat,
        food_count=len(meal.food_entries),
    )


def _recent_foods(meals: list[Meal], limit: int) -> list[RecentFood]:
    rows: list[RecentFood] = []
    for meal in meals:
        for entry in meal.food_entries:
            rows.append(
                RecentFood(
                    food_name=entry.food_name,
                    quantity=entry.quantity,
                    unit=entry.unit,
                    calories=entry.calories,
                    protein=entry.protein,
                    carbohydrates=entry.carbohydrates,
                    fat=entry.fat,
                    consumed_at=meal.consumed_at,
                    meal_id=meal.id,
                    meal_type=meal.meal_type,
                )
            )
    rows.sort(key=lambda item: item.consumed_at, reverse=True)
    return rows[:limit]


def _sum_points(days: list[DayPoint]) -> MacroSnapshot:
    calories = protein = carbs = fat = Decimal("0")
    for point in days:
        calories += point.calories
        protein += point.protein
        carbs += point.carbohydrates
        fat += point.fat
    return MacroSnapshot(calories=calories, protein=protein, carbohydrates=carbs, fat=fat)


def _comparison(
    name: str,
    label: str,
    unit: str,
    actual: Decimal,
    target: Decimal | None,
) -> GoalComparisonItem:
    return GoalComparisonItem(
        name=name,
        label=label,
        unit=unit,
        actual=actual,
        target=target,
        remaining=None if target is None else remaining(target, actual),
        percent=percent_of_target(actual, target),
    )
