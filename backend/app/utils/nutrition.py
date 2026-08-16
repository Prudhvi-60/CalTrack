from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.models import FoodEntry


@dataclass(frozen=True)
class MacroTotals:
    calories: Decimal = Decimal("0")
    protein: Decimal = Decimal("0")
    carbohydrates: Decimal = Decimal("0")
    fat: Decimal = Decimal("0")
    fiber: Decimal = Decimal("0")
    sugar: Decimal = Decimal("0")


@dataclass(frozen=True)
class MicroTotal:
    nutrient_name: str
    amount: Decimal
    unit: str


def sum_food_macros(entries: Iterable[FoodEntry]) -> MacroTotals:
    calories = protein = carbohydrates = fat = fiber = sugar = Decimal("0")
    for entry in entries:
        calories += entry.calories or Decimal("0")
        protein += entry.protein or Decimal("0")
        carbohydrates += entry.carbohydrates or Decimal("0")
        fat += entry.fat or Decimal("0")
        fiber += entry.fiber or Decimal("0")
        sugar += entry.sugar or Decimal("0")
    return MacroTotals(
        calories=calories,
        protein=protein,
        carbohydrates=carbohydrates,
        fat=fat,
        fiber=fiber,
        sugar=sugar,
    )


def remaining(target: Decimal, actual: Decimal) -> Decimal:
    return target - actual


def percent_of_target(actual: Decimal, target: Decimal | None) -> Decimal:
    if target is None or target <= 0:
        return Decimal("0")
    return (actual / target) * Decimal("100")


def sum_micronutrients(entries: Iterable[FoodEntry]) -> list[MicroTotal]:
    amounts: dict[str, Decimal] = {}
    units: dict[str, str] = {}
    for entry in entries:
        for micro in getattr(entry, "micronutrients", []) or []:
            name = micro.nutrient_name
            amounts[name] = amounts.get(name, Decimal("0")) + (micro.amount or Decimal("0"))
            units.setdefault(name, micro.unit)
    return [
        MicroTotal(nutrient_name=name, amount=amounts[name], unit=units[name])
        for name in sorted(amounts)
    ]
