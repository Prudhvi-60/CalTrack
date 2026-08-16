"""Scenario coverage for LLM food JSON. Uses mocked model output, not live vision."""

from app.core.exceptions import AppError
from app.services.ai.pipeline import FoodAnalysisPipeline, parse_label_result, parse_llm_food_result
import pytest


def test_simple_food_image() -> None:
    result = FoodAnalysisPipeline().finalize_llm_photo(
        parse_llm_food_result(
            {
                "foods": [
                    {
                        "name": "banana",
                        "quantity": 1,
                        "unit": "piece",
                        "calories": 105,
                        "protein_g": 1.3,
                        "carbs_g": 27,
                        "fat_g": 0.4,
                        "fiber_g": 3,
                        "sugar_g": 14,
                        "confidence": 0.9,
                    }
                ],
                "confidence": 0.9,
                "notes": "Estimated one visible banana.",
            }
        )
    )
    assert result.food_items[0].name == "banana"
    assert result.food_items[0].calories == 105
    assert result.food_items[0].nutrition_source == "llm"


def test_multiple_food_meal() -> None:
    result = parse_llm_food_result(
        {
            "foods": [
                {
                    "name": "rice",
                    "quantity": 1,
                    "unit": "cup",
                    "calories": 200,
                    "protein_g": 4,
                    "carbs_g": 44,
                    "fat_g": 0.5,
                    "confidence": 0.8,
                },
                {
                    "name": "chicken curry",
                    "quantity": 1,
                    "unit": "cup",
                    "calories": 240,
                    "protein_g": 22,
                    "carbs_g": 8,
                    "fat_g": 12,
                    "confidence": 0.75,
                },
            ],
            "notes": "Estimated two visible dishes.",
        }
    )
    assert len(result.food_items) == 2


def test_indian_meal() -> None:
    result = parse_llm_food_result(
        {
            "meal_type": "lunch",
            "foods": [
                {
                    "name": "dal",
                    "quantity": 1,
                    "unit": "cup",
                    "calories": 180,
                    "protein_g": 12,
                    "carbs_g": 28,
                    "fat_g": 3,
                    "confidence": 0.84,
                },
                {
                    "name": "chapati",
                    "quantity": 2,
                    "unit": "piece",
                    "calories": 140,
                    "protein_g": 4,
                    "carbs_g": 24,
                    "fat_g": 3,
                    "confidence": 0.88,
                },
            ],
            "notes": "Estimated Indian thali items that are visible.",
        }
    )
    names = {item.name for item in result.food_items}
    assert names == {"dal", "chapati"}
    assert result.meal_type == "LUNCH"


def test_packaged_nutrition_label() -> None:
    result = parse_label_result(
        {
            "is_label": True,
            "food_items": [
                {
                    "name": "Instant noodles",
                    "quantity": 1,
                    "unit": "serving",
                    "calories": 380,
                    "protein": 8,
                    "carbohydrates": 52,
                    "fat": 14,
                    "fiber": 2,
                    "sugar": 2,
                    "micronutrients": [{"nutrient_name": "Sodium", "amount": 1480, "unit": "mg"}],
                }
            ],
            "confidence": 0.92,
            "notes": "Read from the printed label.",
            "serving_size": "1 package",
            "servings_per_container": 1,
        }
    )
    assert result.food_items[0].calories == 380
    assert result.serving_size == "1 package"
    assert result.food_items[0].micronutrients[0].nutrient_name == "Sodium"


def test_non_food_image() -> None:
    with pytest.raises(AppError) as exc:
        parse_llm_food_result({"is_food": False, "foods": [], "notes": "Office chair."})
    assert exc.value.code == "NOT_FOOD"


def test_poor_quality_image_keeps_low_confidence() -> None:
    result = FoodAnalysisPipeline().finalize_llm_photo(
        parse_llm_food_result(
            {
                "foods": [
                    {
                        "name": "rice",
                        "quantity": 1,
                        "unit": "bowl",
                        "calories": 180,
                        "protein_g": 4,
                        "carbs_g": 40,
                        "fat_g": 0.5,
                        "confidence": 0.3,
                    }
                ],
                "confidence": 0.3,
                "notes": "Estimated. The photo is blurry so confidence is low.",
            }
        )
    )
    assert result.confidence == 0.3
    assert any("Low confidence" in warning for warning in result.warnings)


def test_multiple_portions() -> None:
    result = parse_llm_food_result(
        {
            "foods": [
                {
                    "name": "idli",
                    "quantity": 3,
                    "unit": "piece",
                    "calories": 120,
                    "protein_g": 4,
                    "carbs_g": 24,
                    "fat_g": 0.6,
                    "confidence": 0.86,
                }
            ],
            "notes": "Estimated three visible idlis.",
        }
    )
    assert result.food_items[0].quantity == 3
