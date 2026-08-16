from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.exceptions import AppError
from app.schemas.ai import VisionFoodPhotoResult
from app.services.ai.pipeline import (
    FoodAnalysisPipeline,
    parse_label_result,
    parse_llm_food_result,
)


def test_llm_calories_are_kept_not_replaced() -> None:
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
                    "fiber_g": 0.6,
                    "sugar_g": 0,
                    "confidence": 0.85,
                }
            ],
            "meal_type": "lunch",
            "confidence": 0.85,
            "notes": "Estimated from the visible bowl.",
        }
    )
    finalized = FoodAnalysisPipeline().finalize_llm_photo(result)
    assert finalized.food_items[0].calories == Decimal("200")
    assert finalized.food_items[0].protein == Decimal("4")
    assert finalized.food_items[0].nutrition_source == "llm"
    assert finalized.meal_type == "LUNCH"
    assert any("LLM estimates" in warning for warning in finalized.warnings)


def test_unknown_name_without_items_is_not_food() -> None:
    with pytest.raises(AppError) as exc:
        parse_llm_food_result({"is_food": False, "foods": [], "notes": "This is a landscape."})
    assert exc.value.code == "NOT_FOOD"


def test_negative_quantity_rejected() -> None:
    with pytest.raises(ValidationError):
        VisionFoodPhotoResult.model_validate(
            {"food_items": [{"name": "rice", "quantity": -1, "unit": "cup", "confidence": 0.9}]}
        )


def test_negative_calories_rejected() -> None:
    with pytest.raises(AppError) as exc:
        parse_llm_food_result(
            {
                "foods": [
                    {
                        "name": "rice",
                        "quantity": 1,
                        "unit": "cup",
                        "calories": -10,
                        "protein_g": 4,
                        "carbs_g": 44,
                        "fat_g": 0.5,
                        "confidence": 0.8,
                    }
                ]
            }
        )
    assert exc.value.code == "AI_INVALID_RESPONSE"


def test_missing_food_name_rejected() -> None:
    with pytest.raises(AppError) as exc:
        parse_llm_food_result({"foods": [{"name": "  ", "quantity": 1, "unit": "cup", "calories": 10, "confidence": 0.9}]})
    assert exc.value.code == "NOT_FOOD"


def test_impossible_quantity_rejected() -> None:
    with pytest.raises(AppError) as exc:
        parse_llm_food_result(
            {
                "foods": [
                    {
                        "name": "rice",
                        "quantity": 99,
                        "unit": "cup",
                        "calories": 200,
                        "protein_g": 4,
                        "carbs_g": 44,
                        "fat_g": 0,
                        "confidence": 0.8,
                    }
                ]
            }
        )
    assert exc.value.code == "AI_INVALID_RESPONSE"


def test_label_values_are_kept() -> None:
    result = parse_label_result(
        {
            "food_items": [
                {
                    "name": "Cereal",
                    "quantity": 1,
                    "unit": "serving",
                    "calories": 110,
                    "protein": 3,
                    "carbohydrates": 24,
                    "fat": 1,
                    "fiber": 3,
                    "sugar": 9,
                    "micronutrients": [{"nutrient_name": "Sodium", "amount": 180, "unit": "mg"}],
                }
            ],
            "confidence": 0.9,
            "notes": "Per serving",
            "serving_size": "3/4 cup",
            "servings_per_container": 12,
        }
    )
    finalized = FoodAnalysisPipeline().finalize_label(result)
    assert finalized.food_items[0].calories == Decimal("110")
    assert finalized.food_items[0].nutrition_source == "label"
    assert finalized.serving_size == "3/4 cup"
