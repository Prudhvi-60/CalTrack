from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.ai import get_vision_service
from app.core.config import get_settings
from app.main import app
from app.schemas.ai import AnalyzedFoodItem, FoodAnalysisResult

MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c089"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _register(client: TestClient) -> tuple[str, dict]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"fb-{uuid4().hex[:12]}@example.com",
            "name": "Feedback User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["user"]


class _FakeVision:
    def analyze_food_image(self, image: bytes, content_type: str) -> FoodAnalysisResult:
        return FoodAnalysisResult(
            analysis_type="food",
            food_items=[
                AnalyzedFoodItem(
                    name="rice",
                    quantity=1,
                    unit="cup",
                    calories=205,
                    protein=4.3,
                    carbohydrates=44.5,
                    fat=0.4,
                )
            ],
            confidence=0.87,
            notes="Estimated from visible portion size.",
            warnings=["AI nutrition values are estimates and must be reviewed before saving."],
        )

    def analyze_nutrition_label(self, image: bytes, content_type: str) -> FoodAnalysisResult:
        return self.analyze_food_image(image, content_type)


def test_corrections_store_confirmed_and_corrected(client: TestClient) -> None:
    token, user = _register(client)
    assert user["allow_training_data_collection"] is False
    response = client.post(
        "/api/v1/ai/corrections",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "analysis_type": "food",
            "items": [
                {
                    "predicted_name": "rice",
                    "predicted_quantity": 1,
                    "predicted_unit": "cup",
                    "corrected_name": "rice",
                    "corrected_quantity": 1,
                    "corrected_unit": "cup",
                    "confirmed": True,
                    "predicted_confidence": 0.9,
                },
                {
                    "predicted_name": "rice",
                    "predicted_quantity": 1,
                    "predicted_unit": "cup",
                    "corrected_name": "rice",
                    "corrected_quantity": 1.5,
                    "corrected_unit": "cup",
                    "confirmed": False,
                    "predicted_confidence": 0.9,
                },
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    assert body[0]["confirmed"] is True
    assert body[1]["confirmed"] is False
    assert body[1]["predicted_quantity"] == 1
    assert body[1]["corrected_quantity"] == 1.5
    assert body[0]["include_in_training"] is False
    assert body[1]["include_in_training"] is False


def test_opt_in_stores_image_and_training_flag(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TRAINING_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    token, _ = _register(client)
    updated = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"allow_training_data_collection": True},
    )
    assert updated.status_code == 200
    assert updated.json()["allow_training_data_collection"] is True
    app.dependency_overrides[get_vision_service] = lambda: _FakeVision()
    try:
        analyze = client.post(
            "/api/v1/ai/analyze-food",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
            data={"analysis_type": "food"},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)
        get_settings.cache_clear()
    assert analyze.status_code == 200, analyze.text
    analysis_id = analyze.json()["analysis_id"]
    assert analysis_id
    images = list((tmp_path / "raw" / "images").glob("*"))
    assert len(images) == 1
    feedback = client.post(
        "/api/v1/ai/corrections",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "analysis_type": "food",
            "analysis_id": analysis_id,
            "items": [
                {
                    "predicted_name": "rice",
                    "predicted_quantity": 1,
                    "predicted_unit": "cup",
                    "corrected_name": "dal",
                    "corrected_quantity": 1,
                    "corrected_unit": "cup",
                    "confirmed": False,
                }
            ],
        },
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()[0]["include_in_training"] is True
    assert feedback.json()[0]["analysis_id"] == analysis_id
