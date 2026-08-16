from decimal import Decimal

from app.services.nutrition_db.calculator import NutritionCalculator
from app.services.nutrition_db.database import default_nutrition_database
from app.services.nutrition_db.portion import PortionEstimator


def test_lookup_and_serving() -> None:
    db = default_nutrition_database()
    rice = db.lookup("white rice")
    assert rice is not None
    assert rice.id == "rice"
    serving = db.get_serving("basmati rice")
    assert serving is not None
    assert serving[1] == Decimal("158")
    names = {food.name for food in db.get_all_foods()}
    assert "dal" in names
    assert "egg" in names


def test_rice_cup_scales_from_100g() -> None:
    db = default_nutrition_database()
    rice = db.lookup("rice")
    assert rice is not None
    portion = PortionEstimator().estimate(rice, Decimal("1"), "cup")
    assert portion.estimated_weight_g == Decimal("158")
    nutrition = NutritionCalculator().calculate(rice, portion.estimated_weight_g)
    assert nutrition.calories == Decimal("205.40")
    assert nutrition.protein == Decimal("4.25")


def test_countable_portions() -> None:
    db = default_nutrition_database()
    chapati = db.lookup("chapatis")
    egg = db.lookup("eggs")
    assert chapati is not None and egg is not None
    two_roti = PortionEstimator().estimate(chapati, Decimal("2"), "piece")
    three_eggs = PortionEstimator().estimate(egg, Decimal("3"), "eggs")
    assert two_roti.estimated_weight_g == Decimal("80")
    assert three_eggs.estimated_weight_g == Decimal("150")
    chapati_n = NutritionCalculator().calculate(chapati, two_roti.estimated_weight_g)
    egg_n = NutritionCalculator().calculate(egg, three_eggs.estimated_weight_g)
    assert chapati_n.calories == Decimal("237.60")
    assert egg_n.calories == Decimal("232.50")
