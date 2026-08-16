from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.nutrition_db.database import FoodRecord

_UNIT_ALIASES = {
    "cups": "cup",
    "cup": "cup",
    "c": "cup",
    "bowl": "bowl",
    "bowls": "bowl",
    "plate": "plate",
    "plates": "plate",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",
    "tbs": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "gram": "g",
    "grams": "g",
    "gm": "g",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
    "l": "ml",
    "liter": "ml",
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "count": "piece",
    "item": "piece",
    "items": "piece",
    "egg": "piece",
    "eggs": "piece",
    "chapati": "piece",
    "chapatis": "piece",
    "roti": "piece",
    "rotis": "piece",
    "idli": "piece",
    "idlis": "piece",
    "vada": "piece",
    "vadas": "piece",
    "dosa": "piece",
    "dosas": "piece",
    "slice": "piece",
    "slices": "piece",
    "medium": "piece",
    "large": "piece",
    "small": "piece",
    "serving": "serving",
    "servings": "serving",
}


@dataclass(frozen=True)
class PortionEstimate:
    quantity: Decimal
    unit: str
    estimated_weight_g: Decimal
    confidence: float
    method: str


def _qty(value: Decimal) -> Decimal:
    return value if value > 0 else Decimal("1")


class PortionEstimator:
    """Converts a visible quantity/unit into grams using reference weights. Not exact."""

    def estimate(self, food: FoodRecord, quantity: Decimal, unit: str) -> PortionEstimate:
        qty = _qty(quantity)
        normalized = _UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())

        if normalized == "g":
            return PortionEstimate(qty, "g", qty, 0.95, "stated-grams")
        if normalized == "kg":
            return PortionEstimate(qty, "kg", qty * Decimal("1000"), 0.95, "stated-kg")
        if normalized == "ml":
            return PortionEstimate(qty, "ml", qty, 0.7, "ml-as-grams")

        if normalized == "piece" or food.portion_kind == "count" and normalized in {"piece", "serving"}:
            unit_g = food.grams_per_unit or food.serving_weight
            return PortionEstimate(qty, unit.strip(), qty * unit_g, 0.8, "countable-unit")

        if normalized == "cup" and food.grams_per_cup:
            return PortionEstimate(qty, "cup", qty * food.grams_per_cup, 0.82, "cup-reference")
        if normalized == "bowl":
            cup = food.grams_per_cup or food.serving_weight
            return PortionEstimate(qty, "bowl", qty * cup * Decimal("1.5"), 0.6, "bowl-as-1.5-cups")
        if normalized == "plate":
            cup = food.grams_per_cup or food.serving_weight
            return PortionEstimate(qty, "plate", qty * cup * Decimal("2"), 0.55, "plate-as-2-cups")
        if normalized == "tbsp":
            if food.id == "oil":
                return PortionEstimate(qty, "tbsp", qty * Decimal("14"), 0.9, "oil-tbsp")
            cup = food.grams_per_cup or food.serving_weight
            return PortionEstimate(qty, "tbsp", qty * (cup / Decimal("16")), 0.65, "tbsp-from-cup")
        if normalized == "tsp":
            cup = food.grams_per_cup or food.serving_weight
            return PortionEstimate(qty, "tsp", qty * (cup / Decimal("48")), 0.6, "tsp-from-cup")
        if normalized == "serving":
            return PortionEstimate(qty, "serving", qty * food.serving_weight, 0.75, "database-serving")

        return PortionEstimate(qty, unit.strip() or "serving", qty * food.serving_weight, 0.5, "fallback-serving")
