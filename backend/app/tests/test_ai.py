from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.ai import get_vision_service
from app.main import app
from app.schemas.ai import AnalyzedFoodItem, FoodAnalysisResult

MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c089"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"ai-{uuid4().hex[:12]}@example.com",
            "name": "AI User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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
                    fiber=0.6,
                    sugar=0,
                )
            ],
            confidence=0.87,
            notes="Estimated from visible portion size.",
            warnings=["AI nutrition values are estimates and must be reviewed before saving."],
        )

    def analyze_nutrition_label(self, image: bytes, content_type: str) -> FoodAnalysisResult:
        return FoodAnalysisResult(
            analysis_type="label",
            food_items=[
                AnalyzedFoodItem(
                    name="Cereal",
                    quantity=1,
                    unit="serving",
                    calories=110,
                    protein=3,
                    carbohydrates=24,
                    fat=1,
                    fiber=3,
                    sugar=9,
                )
            ],
            confidence=0.9,
            notes="Per serving on the label.",
            serving_size="3/4 cup",
            servings_per_container=12,
            warnings=["AI nutrition values are estimates and must be reviewed before saving."],
        )


def test_analyze_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/analyze-food",
        files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
    )
    assert response.status_code == 401


def test_analyze_rejects_non_image(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/ai/analyze-food",
        headers=_auth(token),
        files={"file": ("notes.txt", BytesIO(b"hello world"), "text/plain")},
        data={"analysis_type": "food"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_analyze_rejects_mismatched_bytes(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/ai/analyze-food",
        headers=_auth(token),
        files={"file": ("food.jpg", BytesIO(b"not-a-jpeg"), "image/jpeg")},
        data={"analysis_type": "food"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_analyze_rejects_oversized_dimensions(client: TestClient) -> None:
    token = _register(client)
    huge = bytearray(MIN_PNG)
    huge[16:24] = (20000).to_bytes(4, "big") + (20000).to_bytes(4, "big")
    response = client.post(
        "/api/v1/ai/analyze-food",
        headers=_auth(token),
        files={"file": ("food.png", BytesIO(bytes(huge)), "image/png")},
        data={"analysis_type": "food"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE"


def test_analyze_rejects_oversize(client: TestClient, monkeypatch) -> None:
    token = _register(client)

    class Limits:
        ai_max_upload_bytes = 10

    monkeypatch.setattr("app.services.ai.analyze_service.get_settings", lambda: Limits())
    response = client.post(
        "/api/v1/ai/analyze-food",
        headers=_auth(token),
        files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
        data={"analysis_type": "food"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_analyze_food_success(client: TestClient) -> None:
    token = _register(client)
    app.dependency_overrides[get_vision_service] = lambda: _FakeVision()
    try:
        response = client.post(
            "/api/v1/ai/analyze-food",
            headers=_auth(token),
            files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
            data={"analysis_type": "food"},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["food_items"][0]["name"] == "rice"
    assert body["confidence"] == 0.87
    assert "estimates" in body["warnings"][0].lower() or "estimates" in " ".join(body["warnings"]).lower()


def test_analyze_label_success(client: TestClient) -> None:
    token = _register(client)
    app.dependency_overrides[get_vision_service] = lambda: _FakeVision()
    try:
        response = client.post(
            "/api/v1/ai/analyze-food",
            headers=_auth(token),
            files={"file": ("label.png", BytesIO(MIN_PNG), "image/png")},
            data={"analysis_type": "label"},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["analysis_type"] == "label"
    assert body["food_items"][0]["name"] == "Cereal"
    assert body["serving_size"] == "3/4 cup"


def test_analyze_not_configured(client: TestClient) -> None:
    token = _register(client)
    from app.core.config import Settings
    from app.services.ai.vision_service import VisionService

    app.dependency_overrides[get_vision_service] = lambda: VisionService(
        settings=Settings(_env_file=None, ai_api_key="")
    )
    try:
        response = client.post(
            "/api/v1/ai/analyze-food",
            headers=_auth(token),
            files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
            data={"analysis_type": "food"},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_NOT_CONFIGURED"


def test_analyze_does_not_create_a_meal(client: TestClient) -> None:
    token = _register(client)
    app.dependency_overrides[get_vision_service] = lambda: _FakeVision()
    try:
        client.post(
            "/api/v1/ai/analyze-food",
            headers=_auth(token),
            files={"file": ("food.png", BytesIO(MIN_PNG), "image/png")},
            data={"analysis_type": "food"},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)
    meals = client.get("/api/v1/meals", headers=_auth(token))
    assert meals.json()["total"] == 0
