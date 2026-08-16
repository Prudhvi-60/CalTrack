from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.nutrition_db.database import FoodRecord, MicroRef

_QUANTUM = Decimal("0.01")
_MICRO_QUANTUM = Decimal("0.0001")
_MAX_CALORIES = Decimal("2500")
_MAX_WEIGHT = Decimal("2000")


@dataclass(frozen=True)
class CalculatedNutrition:
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal
    sugar: Decimal
    micronutrients: tuple[MicroRef, ...]
    scale: Decimal


def _round(value: Decimal, quantum: Decimal = _QUANTUM) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


class NutritionCalculator:
    """Scales per-100g (or per_g) database values by estimated weight."""

    def calculate(self, food: FoodRecord, weight_g: Decimal) -> CalculatedNutrition:
        if weight_g <= 0:
            weight_g = food.serving_weight
        if weight_g > _MAX_WEIGHT:
            raise ValueError("estimated portion is implausibly large")
        scale = weight_g / food.per_g
        calories = _round(food.calories * scale)
        if calories > _MAX_CALORIES:
            raise ValueError("calculated calories are implausibly large")
        micros = tuple(
            MicroRef(
                nutrient_name=micro.nutrient_name,
                amount=_round(micro.amount * scale, _MICRO_QUANTUM),
                unit=micro.unit,
            )
            for micro in food.micronutrients
        )
        return CalculatedNutrition(
            calories=calories,
            protein=_round(food.protein * scale),
            carbohydrates=_round(food.carbohydrates * scale),
            fat=_round(food.fat * scale),
            fiber=_round(food.fiber * scale),
            sugar=_round(food.sugar * scale),
            micronutrients=micros,
            scale=scale,
        )
