from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from app.services.nutrition_db.normalizer import FoodNormalizer, NormalizeResult

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_MATCH_MIN = 0.72


@dataclass(frozen=True)
class MicroRef:
    nutrient_name: str
    amount: Decimal
    unit: str


@dataclass(frozen=True)
class FoodRecord:
    id: str
    name: str
    category: str
    portion_kind: str
    per_g: Decimal
    calories: Decimal
    protein: Decimal
    carbohydrates: Decimal
    fat: Decimal
    fiber: Decimal
    sugar: Decimal
    serving: str
    serving_weight: Decimal
    grams_per_cup: Decimal | None
    grams_per_unit: Decimal | None
    source: str
    micronutrients: tuple[MicroRef, ...]


@dataclass(frozen=True)
class FoodMatch:
    food: FoodRecord
    normalize: NormalizeResult
    confidence: float


def _dec(value: object) -> Decimal:
    return Decimal(str(value))


def _load_foods() -> list[FoodRecord]:
    payload = json.loads((_DATA_DIR / "nutrition_foods.json").read_text(encoding="utf-8"))
    foods: list[FoodRecord] = []
    for item in payload["foods"]:
        micros = tuple(
            MicroRef(
                nutrient_name=micro["nutrient_name"],
                amount=_dec(micro["amount"]),
                unit=micro["unit"],
            )
            for micro in item.get("micronutrients") or []
        )
        foods.append(
            FoodRecord(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                portion_kind=item["portion_kind"],
                per_g=_dec(item["per_g"]),
                calories=_dec(item["calories"]),
                protein=_dec(item["protein"]),
                carbohydrates=_dec(item["carbohydrates"]),
                fat=_dec(item["fat"]),
                fiber=_dec(item["fiber"]),
                sugar=_dec(item["sugar"]),
                serving=item["serving"],
                serving_weight=_dec(item["serving_weight"]),
                grams_per_cup=_dec(item["grams_per_cup"]) if item.get("grams_per_cup") is not None else None,
                grams_per_unit=_dec(item["grams_per_unit"]) if item.get("grams_per_unit") is not None else None,
                source=item["source"],
                micronutrients=micros,
            )
        )
    return foods


class NutritionDatabase:
    def __init__(self, foods: list[FoodRecord] | None = None) -> None:
        self._foods = foods if foods is not None else _cached_foods()
        self._by_name = {food.name: food for food in self._foods}
        self._by_id = {food.id: food for food in self._foods}
        self._normalizer = FoodNormalizer([food.name for food in self._foods] + [food.id for food in self._foods])

    def get_all_foods(self) -> list[FoodRecord]:
        return list(self._foods)

    def get_serving(self, name: str) -> tuple[str, Decimal] | None:
        match = self.find_food(name)
        if match is None:
            return None
        return match.food.serving, match.food.serving_weight

    def lookup(self, name: str) -> FoodRecord | None:
        match = self.find_food(name)
        return match.food if match else None

    def find_food(self, name: str) -> FoodMatch | None:
        result = self._normalizer.normalize(name)
        if result.method == "empty":
            return None
        food = self._by_name.get(result.canonical) or self._by_id.get(result.canonical.replace(" ", "_"))
        if food is None:
            return None
        if result.confidence < _MATCH_MIN:
            return None
        return FoodMatch(food=food, normalize=result, confidence=result.confidence)


@lru_cache(maxsize=1)
def _cached_foods() -> tuple[FoodRecord, ...]:
    return tuple(_load_foods())


def default_nutrition_database() -> NutritionDatabase:
    return NutritionDatabase()
