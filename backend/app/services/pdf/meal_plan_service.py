from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import User
from app.models.enums import MealType
from app.schemas.meal import FoodEntryCreate, MealCreate
from app.schemas.meal_plan import (
    MealPlanConfirmRequest,
    MealPlanConfirmResponse,
    MealPlanDay,
    MealPlanFood,
    MealPlanPreviewResponse,
)
from app.services.meal_service import MealService
from app.services.nutrition_db.calculator import NutritionCalculator
from app.services.nutrition_db.database import default_nutrition_database
from app.services.nutrition_db.portion import PortionEstimator
from app.services.pdf.meal_plan_extractor import MealPlanExtractor
from app.services.pdf.meal_slots import SLOT_KEYS, slot_clock, slot_label, slot_to_meal_type
from app.services.pdf.text_extractor import extract_pdf_document, sanitize_pdf_filename

_ZERO = Decimal("0")


class MealPlanService:
    def __init__(
        self,
        db: Session,
        user: User,
        extractor: MealPlanExtractor | None = None,
    ) -> None:
        self.user = user
        self.meals = MealService(db, user)
        self.extractor = extractor or MealPlanExtractor()
        self.database = default_nutrition_database()
        self.portion = PortionEstimator()
        self.calculator = NutritionCalculator()

    def preview(self, data: bytes, filename: str | None, content_type: str | None) -> MealPlanPreviewResponse:
        settings = get_settings()
        sanitize_pdf_filename(filename)
        _validate_upload(data, content_type, settings.ai_max_upload_bytes)
        document = extract_pdf_document(data)
        extracted = self.extractor.extract(document)
        days = [_enrich_day(day, self._match_food) for day in extracted.days]
        return extracted.model_copy(update={"days": days})

    def confirm(self, payload: MealPlanConfirmRequest) -> MealPlanConfirmResponse:
        grouped: dict[tuple[date, MealType, str], list[FoodEntryCreate]] = defaultdict(list)
        notes_by_key: dict[tuple[date, MealType, str], list[str]] = defaultdict(list)
        foods = 0
        for day in payload.days:
            if not day.include:
                continue
            for item in day.foods:
                if not item.include:
                    continue
                slot = item.slot
                meal_type = slot_to_meal_type(slot)
                quantity = item.quantity if item.quantity is not None and item.quantity > 0 else Decimal("1")
                unit = (item.unit or "serving")[:40]
                calories = item.calories if item.calories is not None else _ZERO
                protein = item.protein if item.protein is not None else _ZERO
                carbs = item.carbohydrates if item.carbohydrates is not None else _ZERO
                fat = item.fat if item.fat is not None else _ZERO
                key = (day.date, meal_type, slot)
                grouped[key].append(
                    FoodEntryCreate(
                        food_name=item.food,
                        quantity=quantity,
                        unit=unit,
                        calories=calories,
                        protein=protein,
                        carbohydrates=carbs,
                        fat=fat,
                        fiber=item.fiber if item.fiber is not None else _ZERO,
                        sugar=item.sugar if item.sugar is not None else _ZERO,
                    )
                )
                label = item.original_label or slot_label(slot)
                note_bits = [f"Imported meal plan ({label})"]
                if day.day:
                    note_bits.append(f"Day {day.day}")
                if item.meal_name:
                    note_bits.append(item.meal_name)
                if item.alternative:
                    note_bits.append(f"or {item.alternative}")
                if item.notes:
                    note_bits.append(item.notes)
                notes_by_key[key].append("; ".join(note_bits))
                foods += 1
        if foods == 0:
            raise AppError("INVALID_IMPORT", "Select at least one food to import.", 400)
        created = []
        for (day, meal_type, slot), entries in grouped.items():
            hour, minute = slot_clock(slot)
            consumed_at = datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)
            note = notes_by_key[(day, meal_type, slot)][0][:2000]
            created.append(
                self.meals.create(
                    MealCreate(
                        meal_type=meal_type,
                        consumed_at=consumed_at,
                        notes=note,
                        food_entries=entries,
                    )
                )
            )
        return MealPlanConfirmResponse(
            imported_meals=len(created),
            imported_foods=foods,
            meals=created,
            meal_types=[meal.meal_type for meal in created],
        )

    def _match_food(self, food: MealPlanFood) -> MealPlanFood:
        match = self.database.find_food(food.food)
        if match is None or food.quantity is None or food.quantity <= 0:
            return food.model_copy(update={"nutrition_status": "unknown"})
        try:
            portion = self.portion.estimate(match.food, food.quantity, food.unit or "serving")
            nutrition = self.calculator.calculate(match.food, portion.estimated_weight_g)
        except Exception:
            return food.model_copy(update={"nutrition_status": "unknown", "matched_food": match.food.name})
        return food.model_copy(
            update={
                "nutrition_status": "matched",
                "matched_food": match.food.name,
                "calories": nutrition.calories,
                "protein": nutrition.protein,
                "carbohydrates": nutrition.carbohydrates,
                "fat": nutrition.fat,
                "fiber": nutrition.fiber,
                "sugar": nutrition.sugar,
            }
        )


def _validate_upload(data: bytes, content_type: str | None, max_bytes: int) -> None:
    if not data:
        raise AppError("INVALID_PDF", "The uploaded file is empty", 400)
    if len(data) > max_bytes:
        raise AppError("FILE_TOO_LARGE", "PDF must be 5 MB or smaller", 413)
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime and mime not in {"application/pdf", "application/x-pdf", "application/octet-stream"}:
        raise AppError("INVALID_PDF", "Upload a PDF file", 400)


def _enrich_day(day: MealPlanDay, matcher) -> MealPlanDay:
    meals = day.meals
    updated = {}
    for key in SLOT_KEYS:
        updated[key] = [matcher(food) for food in getattr(meals, key)]
    resolved_date = day.date
    if resolved_date is None and day.day:
        resolved_date = date.today() + timedelta(days=day.day - 1)
    return day.model_copy(update={"date": resolved_date, "meals": meals.model_copy(update=updated)})
