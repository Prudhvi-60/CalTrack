from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import FoodEntry, Meal
from app.models.enums import MealType
from app.utils.nutrition import MacroTotals
from app.utils.validators import escape_like, utc_day_start, utc_exclusive_end


class MealRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _detail_options(self):
        return (selectinload(Meal.food_entries).selectinload(FoodEntry.micronutrients),)

    def _list_options(self):
        return (selectinload(Meal.food_entries),)

    def get_for_user(self, user_id: int, meal_id: int) -> Meal | None:
        stmt = (
            select(Meal)
            .options(*self._detail_options())
            .where(Meal.id == meal_id, Meal.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: int,
        *,
        page: int,
        page_size: int,
        meal_type: MealType | None,
        on_date: date | None,
        start_date: date | None,
        end_date: date | None,
        search: str | None,
    ) -> tuple[list[Meal], int]:
        filters = self._filters(user_id, meal_type, on_date, start_date, end_date, search)
        total = self.db.scalar(select(func.count()).select_from(Meal).where(*filters)) or 0
        stmt = (
            select(Meal)
            .options(*self._list_options())
            .where(*filters)
            .order_by(Meal.consumed_at.desc(), Meal.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.execute(stmt).scalars().unique())
        return items, int(total)

    def list_in_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        *,
        include_micros: bool = False,
    ) -> list[Meal]:
        filters = self._filters(
            user_id,
            meal_type=None,
            on_date=None,
            start_date=start_date,
            end_date=end_date,
            search=None,
        )
        options = self._detail_options() if include_micros else self._list_options()
        stmt = (
            select(Meal)
            .options(*options)
            .where(*filters)
            .order_by(Meal.consumed_at.asc(), Meal.id.asc())
        )
        return list(self.db.execute(stmt).scalars().unique())

    def macros_by_day(self, user_id: int, start_date: date, end_date: date) -> dict[date, MacroTotals]:
        day_expr = cast(func.timezone("UTC", Meal.consumed_at), Date)
        filters = self._filters(
            user_id,
            meal_type=None,
            on_date=None,
            start_date=start_date,
            end_date=end_date,
            search=None,
        )
        stmt = (
            select(
                day_expr.label("day"),
                func.coalesce(func.sum(FoodEntry.calories), 0).label("calories"),
                func.coalesce(func.sum(FoodEntry.protein), 0).label("protein"),
                func.coalesce(func.sum(FoodEntry.carbohydrates), 0).label("carbohydrates"),
                func.coalesce(func.sum(FoodEntry.fat), 0).label("fat"),
                func.coalesce(func.sum(FoodEntry.fiber), 0).label("fiber"),
                func.coalesce(func.sum(FoodEntry.sugar), 0).label("sugar"),
            )
            .join(FoodEntry, FoodEntry.meal_id == Meal.id)
            .where(*filters)
            .group_by(day_expr)
        )
        rows = self.db.execute(stmt).all()
        result: dict[date, MacroTotals] = {}
        for row in rows:
            day_value = row.day.date() if isinstance(row.day, datetime) else row.day
            result[day_value] = MacroTotals(
                calories=Decimal(str(row.calories)),
                protein=Decimal(str(row.protein)),
                carbohydrates=Decimal(str(row.carbohydrates)),
                fat=Decimal(str(row.fat)),
                fiber=Decimal(str(row.fiber)),
                sugar=Decimal(str(row.sugar)),
            )
        return result

    def create(self, meal: Meal) -> Meal:
        self.db.add(meal)
        self.db.flush()
        return meal

    def delete(self, meal: Meal) -> None:
        self.db.delete(meal)
        self.db.flush()

    def _filters(
        self,
        user_id: int,
        meal_type: MealType | None,
        on_date: date | None,
        start_date: date | None,
        end_date: date | None,
        search: str | None,
    ) -> list[object]:
        filters: list[object] = [Meal.user_id == user_id]
        if meal_type is not None:
            filters.append(Meal.meal_type == meal_type)
        if on_date is not None:
            filters.append(Meal.consumed_at >= utc_day_start(on_date))
            filters.append(Meal.consumed_at < utc_exclusive_end(on_date))
        else:
            if start_date is not None:
                filters.append(Meal.consumed_at >= utc_day_start(start_date))
            if end_date is not None:
                filters.append(Meal.consumed_at < utc_exclusive_end(end_date))
        if search:
            pattern = f"%{escape_like(search.strip())}%"
            filters.append(Meal.food_entries.any(FoodEntry.food_name.ilike(pattern, escape="\\")))
        return filters
