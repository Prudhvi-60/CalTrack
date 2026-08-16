from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FoodEntry, Goal, Meal
from app.utils.nutrition import MacroTotals, sum_food_macros


class GoalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_user(self, user_id: int) -> Goal | None:
        stmt = select(Goal).where(Goal.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: int, *, offset: int, limit: int) -> tuple[list[Goal], int]:
        total = self.db.scalar(select(func.count()).select_from(Goal).where(Goal.user_id == user_id)) or 0
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id)
            .order_by(Goal.id)
            .offset(offset)
            .limit(limit)
        )
        items = list(self.db.execute(stmt).scalars())
        return items, int(total)

    def create(self, user_id: int, **values: object) -> Goal:
        goal = Goal(user_id=user_id, **values)
        self.db.add(goal)
        self.db.flush()
        self.db.refresh(goal)
        return goal

    def delete(self, goal: Goal) -> None:
        self.db.delete(goal)
        self.db.flush()

    def todays_macros(self, user_id: int, day: date) -> MacroTotals:
        start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        stmt = (
            select(FoodEntry)
            .join(Meal, FoodEntry.meal_id == Meal.id)
            .where(
                Meal.user_id == user_id,
                Meal.consumed_at >= start,
                Meal.consumed_at < end,
            )
        )
        entries = list(self.db.execute(stmt).scalars())
        return sum_food_macros(entries)
