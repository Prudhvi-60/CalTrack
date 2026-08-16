"""Validates LLM nutrition JSON fixtures. Does not claim live vision accuracy."""

from app.services.ai.pipeline import parse_llm_food_result


def test_evaluation_fixtures_for_llm_nutrition_json() -> None:
    cases = [
        {
            "name": "rice",
            "calories": 205,
            "payload": {
                "foods": [
                    {
                        "name": "rice",
                        "quantity": 1,
                        "unit": "cup",
                        "calories": 205,
                        "protein_g": 4.3,
                        "carbs_g": 45,
                        "fat_g": 0.4,
                        "confidence": 0.91,
                    }
                ],
                "notes": "Estimated bowl of rice.",
            },
        },
        {
            "name": "dal",
            "calories": 198,
            "payload": {
                "foods": [
                    {
                        "name": "dal",
                        "quantity": 1,
                        "unit": "cup",
                        "calories": 198,
                        "protein_g": 12,
                        "carbs_g": 28,
                        "fat_g": 4,
                        "confidence": 0.88,
                    }
                ],
                "notes": "Estimated yellow dal.",
            },
        },
        {
            "name": "chapati",
            "calories": 140,
            "payload": {
                "foods": [
                    {
                        "name": "chapati",
                        "quantity": 2,
                        "unit": "piece",
                        "calories": 140,
                        "protein_g": 4,
                        "carbs_g": 24,
                        "fat_g": 3,
                        "confidence": 0.9,
                    }
                ],
                "notes": "Estimated two rotis.",
            },
        },
    ]
    for case in cases:
        result = parse_llm_food_result(case["payload"])
        assert result.food_items[0].name == case["name"]
        assert float(result.food_items[0].calories) == case["calories"]
        assert result.food_items[0].nutrition_source == "llm"
