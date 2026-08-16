from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import FoodEntry, Meal, Micronutrient, User
from app.models.enums import MealType
from app.repositories.meal_repository import MealRepository
from app.schemas.meal import FoodEntryCreate, MealCreate, MealPublic, MealTotals, MealUpdate
from app.utils.nutrition import sum_food_macros
from app.utils.pagination import PaginatedResponse, paginated


class MealService:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.meals = MealRepository(db)

    def list_meals(
        self,
        *,
        page: int,
        page_size: int,
        meal_type: MealType | None,
        on_date: date | None,
        start_date: date | None,
        end_date: date | None,
        search: str | None,
    ) -> PaginatedResponse[MealPublic]:
        if start_date and end_date and start_date > end_date:
            raise AppError("VALIDATION_ERROR", "start_date must be on or before end_date", 422)
        items, total = self.meals.list_for_user(
            self.user.id,
            page=page,
            page_size=page_size,
            meal_type=meal_type,
            on_date=on_date,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        return paginated(
            [self._to_public(meal) for meal in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get(self, meal_id: int) -> MealPublic:
        return self._to_public(self._require(meal_id))

    def create(self, payload: MealCreate) -> MealPublic:
        meal = Meal(
            user_id=self.user.id,
            meal_type=payload.meal_type,
            consumed_at=payload.consumed_at,
            notes=payload.notes,
            food_entries=[self._entry_from_schema(entry) for entry in payload.food_entries],
        )
        self.meals.create(meal)
        self.db.commit()
        loaded = self._require(meal.id)
        return self._to_public(loaded)

    def replace(self, meal_id: int, payload: MealUpdate) -> MealPublic:
        meal = self._require(meal_id)
        meal.meal_type = payload.meal_type
        meal.consumed_at = payload.consumed_at
        meal.notes = payload.notes
        meal.food_entries.clear()
        self.db.flush()
        for entry in payload.food_entries:
            meal.food_entries.append(self._entry_from_schema(entry))
        self.db.commit()
        return self._to_public(self._require(meal.id))

    def delete(self, meal_id: int) -> None:
        meal = self._require(meal_id)
        self.meals.delete(meal)
        self.db.commit()

    def add_food(self, meal_id: int, entry: FoodEntryCreate) -> MealPublic:
        meal = self._require(meal_id)
        meal.food_entries.append(self._entry_from_schema(entry))
        self.db.commit()
        return self._to_public(self._require(meal.id))

    def _require(self, meal_id: int) -> Meal:
        meal = self.meals.get_for_user(self.user.id, meal_id)
        if meal is None:
            raise AppError("RESOURCE_NOT_FOUND", "Meal not found", 404)
        return meal

    def _entry_from_schema(self, entry: FoodEntryCreate) -> FoodEntry:
        food = FoodEntry(
            food_name=entry.food_name.strip(),
            quantity=entry.quantity,
            unit=entry.unit.strip(),
            calories=entry.calories,
            protein=entry.protein,
            carbohydrates=entry.carbohydrates,
            fat=entry.fat,
            fiber=entry.fiber,
            sugar=entry.sugar,
        )
        for micro in entry.micronutrients:
            food.micronutrients.append(
                Micronutrient(
                    nutrient_name=micro.nutrient_name.value,
                    amount=micro.amount,
                    unit=micro.unit.strip(),
                )
            )
        return food

    def _to_public(self, meal: Meal) -> MealPublic:
        totals = sum_food_macros(meal.food_entries)
        return MealPublic(
            id=meal.id,
            user_id=meal.user_id,
            meal_type=meal.meal_type,
            consumed_at=meal.consumed_at,
            notes=meal.notes,
            food_entries=list(meal.food_entries),
            totals=MealTotals(
                calories=totals.calories,
                protein=totals.protein,
                carbohydrates=totals.carbohydrates,
                fat=totals.fat,
                fiber=totals.fiber,
                sugar=totals.sugar,
            ),
            created_at=meal.created_at,
            updated_at=meal.updated_at,
        )
