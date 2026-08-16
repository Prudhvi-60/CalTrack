from decimal import Decimal
from types import SimpleNamespace

from app.utils.nutrition import percent_of_target, remaining, sum_food_macros, sum_micronutrients


def test_sum_food_macros() -> None:
    entries = [
        SimpleNamespace(
            calories=Decimal("100"),
            protein=Decimal("10"),
            carbohydrates=Decimal("20"),
            fat=Decimal("5"),
            fiber=Decimal("2"),
            sugar=Decimal("1"),
        ),
        SimpleNamespace(
            calories=Decimal("50.5"),
            protein=Decimal("2.5"),
            carbohydrates=Decimal("8"),
            fat=Decimal("1.5"),
            fiber=Decimal("0"),
            sugar=Decimal("3"),
        ),
    ]
    totals = sum_food_macros(entries)
    assert totals.calories == Decimal("150.5")
    assert totals.protein == Decimal("12.5")
    assert totals.carbohydrates == Decimal("28")
    assert totals.fat == Decimal("6.5")


def test_remaining_can_be_negative() -> None:
    assert remaining(Decimal("100"), Decimal("80")) == Decimal("20")
    assert remaining(Decimal("100"), Decimal("120")) == Decimal("-20")


def test_percent_of_target() -> None:
    assert percent_of_target(Decimal("50"), Decimal("100")) == Decimal("50")
    assert percent_of_target(Decimal("10"), Decimal("0")) == Decimal("0")


def test_sum_micronutrients() -> None:
    entries = [
        SimpleNamespace(
            micronutrients=[
                SimpleNamespace(nutrient_name="Iron", amount=Decimal("1.5"), unit="mg"),
                SimpleNamespace(nutrient_name="Calcium", amount=Decimal("100"), unit="mg"),
            ]
        ),
        SimpleNamespace(
            micronutrients=[
                SimpleNamespace(nutrient_name="Iron", amount=Decimal("0.5"), unit="mg"),
            ]
        ),
    ]
    totals = {item.nutrient_name: item for item in sum_micronutrients(entries)}
    assert totals["Iron"].amount == Decimal("2.0")
    assert totals["Calcium"].amount == Decimal("100")
