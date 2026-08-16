import json

import pytest

from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.ai.gemini_client import map_gemini_error
from app.services.ai.pipeline import coerce_label_payload, parse_llm_food_result
from app.services.ai.vision_service import VisionService, _extract_json
from app.utils.images import sniff_image_kind

MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c089"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def test_sniff_png() -> None:
    assert sniff_image_kind(MIN_PNG) == "png"
    assert sniff_image_kind(b"nope") is None


def test_extract_json_from_fence() -> None:
    payload = _extract_json('```json\n{"food_items": []}\n```')
    assert payload["food_items"] == []


def test_extract_json_rejects_garbage() -> None:
    with pytest.raises(AppError) as exc:
        _extract_json("not json")
    assert exc.value.code == "AI_INVALID_RESPONSE"


def test_coerce_drops_unknown_micronutrients() -> None:
    raw = {
        "food_items": [
            {
                "name": "milk",
                "quantity": 1,
                "unit": "cup",
                "calories": 100,
                "protein": 8,
                "carbohydrates": 12,
                "fat": 2,
                "micronutrients": [
                    {"nutrient_name": "Calcium", "amount": 300, "unit": "mg"},
                    {"nutrient_name": "Unobtanium", "amount": 1, "unit": "mg"},
                ],
            }
        ],
        "confidence": 0.8,
        "notes": "",
    }
    cleaned = coerce_label_payload(raw)
    names = [item["nutrient_name"] for item in cleaned["food_items"][0]["micronutrients"]]
    assert names == ["Calcium"]


def _food_payload(confidence: float = 0.9) -> dict:
    return {
        "foods": [
            {
                "name": "apple",
                "quantity": 1,
                "unit": "piece",
                "calories": 95,
                "protein_g": 0.5,
                "carbs_g": 25,
                "fat_g": 0.3,
                "fiber_g": 4,
                "sugar_g": 19,
                "confidence": confidence,
            }
        ],
        "confidence": confidence,
        "notes": "Estimated from a visible whole apple.",
    }


def _service(completer, **kwargs) -> VisionService:
    return VisionService(
        settings=Settings(_env_file=None, ai_api_key="test-key", ai_model="gemini-2.5-flash-lite", **kwargs),
        completer=completer,
    )


def test_vision_not_configured() -> None:
    service = VisionService(settings=Settings(_env_file=None, ai_api_key=""))
    with pytest.raises(AppError) as exc:
        service.analyze_food_image(MIN_PNG, "image/png")
    assert exc.value.code == "AI_NOT_CONFIGURED"


def test_gemini_unauthorized_maps_without_exposing_key() -> None:
    class FakeError(Exception):
        code = 401

        def __str__(self) -> str:
            return "API key AIzaSyFakeKeyValue1234567890 was rejected"

    error = map_gemini_error(FakeError())
    assert error.code == "AI_UNAUTHORIZED"
    assert "AIza" not in error.message


def test_gemini_rate_limit_maps_to_429() -> None:
    class FakeError(Exception):
        code = 429

    error = map_gemini_error(FakeError())
    assert error.code == "AI_RATE_LIMIT"
    assert error.status_code == 429


def test_chat_http_400_is_not_an_image_error() -> None:
    class FakeError(Exception):
        code = 400

        def __str__(self) -> str:
            return "invalid argument"

    error = map_gemini_error(FakeError(), source="chat")
    assert error.code == "AI_PROVIDER_ERROR"
    assert "image" not in error.message.lower()


def test_vision_invalid_json() -> None:
    def completer(_prompt: str, _image: bytes, _content_type: str) -> dict:
        raise AppError("AI_INVALID_RESPONSE", "AI did not return valid JSON", 502)

    with pytest.raises(AppError) as exc:
        _service(completer).analyze_food_image(MIN_PNG, "image/png")
    assert exc.value.code == "AI_INVALID_RESPONSE"


def test_vision_low_confidence_warning() -> None:
    def completer(_prompt: str, _image: bytes, _content_type: str) -> dict:
        return _food_payload(0.2)

    result = _service(completer, ai_min_confidence=0.5).analyze_food_image(MIN_PNG, "image/png")
    assert result.food_items[0].nutrition_source == "llm"
    assert result.food_items[0].calories == 95
    assert any("Low confidence" in warning for warning in result.warnings)


def test_vision_non_food_image() -> None:
    def completer(_prompt: str, _image: bytes, _content_type: str) -> dict:
        return {"is_food": False, "foods": [], "notes": "This is a photo of a cat, not food."}

    with pytest.raises(AppError) as exc:
        _service(completer).analyze_food_image(MIN_PNG, "image/png")
    assert exc.value.code == "NOT_FOOD"


def test_parse_accepts_example_schema() -> None:
    result = parse_llm_food_result(
        {
            "meal_type": "lunch",
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
            "total": {"calories": 200, "protein_g": 4, "carbs_g": 44, "fat_g": 0.5, "fiber_g": 0.6, "sugar_g": 0},
        }
    )
    assert result.food_items[0].carbohydrates == 44


def test_gemini_client_is_reused_and_not_closed_between_calls() -> None:
    from app.services.ai.gemini_client import close_gemini_client, get_gemini_client

    close_gemini_client()
    settings = Settings(_env_file=None, ai_api_key="test-key", ai_model="gemini-2.5-flash-lite")
    first = get_gemini_client(settings)
    second = get_gemini_client(settings)
    assert first is second
    close_gemini_client()
