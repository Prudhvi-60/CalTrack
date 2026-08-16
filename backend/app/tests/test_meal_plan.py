from io import BytesIO
from uuid import uuid4

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.pdf import _meal_plan_service
from app.core.dependencies import get_current_user
from app.core.exceptions import AppError
from app.db.session import get_db
from app.main import app
from app.models import User
from app.services.pdf.meal_plan_extractor import MealPlanExtractor, _parse_food
from app.services.pdf.meal_plan_service import MealPlanService
from app.services.pdf.meal_slots import normalize_slot
from app.services.pdf.text_extractor import extract_pdf_document, sanitize_pdf_filename
from app.tests.test_pdf import CSV, _pdf_from_text


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"plan-{uuid4().hex[:12]}@example.com", "name": "Plan User", "password": "SecurePass1!"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _plan_pdf(body: str) -> bytes:
    padding = "Meal plan food diary nutrition schedule with breakfast lunch dinner snacks. "
    return _pdf_from_text(padding * 3 + body)


def _payload(**overrides):
    base = {
        "document_type": "meal_plan",
        "title": "Sample plan",
        "days": [
            {
                "day": 1,
                "date": None,
                "label": "Day 1",
                "meals": {
                    "breakfast": [
                        {"food": "eggs", "quantity": 2, "unit": "piece", "original_label": "Morning meal"},
                        {"food": "toast", "quantity": 1, "unit": "slice"},
                    ],
                    "morning_snack": [
                        {"food": "apple", "quantity": "3/4", "unit": "cup", "original_label": "Mid-morning snack"}
                    ],
                    "lunch": [{"food": "chicken", "quantity": 4, "unit": "oz"}],
                    "evening_snack": [
                        {"food": "yogurt", "quantity": 1, "unit": "cup", "original_label": "Afternoon snack"}
                    ],
                    "dinner": [
                        {
                            "food": "broccoli",
                            "quantity": 1,
                            "unit": "cup",
                            "meal_name": "Chicken and Vegetable Stir-Fry",
                        }
                    ],
                    "other": [],
                },
            }
        ],
    }
    base.update(overrides)
    return base


def _override(completer):
    def meal_plan_service(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> MealPlanService:
        return MealPlanService(db, user, extractor=MealPlanExtractor(completer=completer))

    app.dependency_overrides[_meal_plan_service] = meal_plan_service


def test_sanitize_filename() -> None:
    assert sanitize_pdf_filename("plan.pdf") == "plan.pdf"
    try:
        sanitize_pdf_filename("notes.txt")
        raise AssertionError("expected invalid extension")
    except AppError as exc:
        assert exc.code == "INVALID_PDF"


def test_normalize_slot_aliases() -> None:
    assert normalize_slot("Mid-morning snack") == "morning_snack"
    assert normalize_slot("PM snack") == "evening_snack"
    assert normalize_slot("Morning meal") == "breakfast"
    assert normalize_slot("Dessert") == "other"


def test_parse_fraction_and_range() -> None:
    food = _parse_food({"food": "blueberries", "quantity": "3/4", "unit": "cup"}, "Breakfast")
    assert food is not None
    assert food.quantity == food.quantity
    assert float(food.quantity) == 0.75
    ranged = _parse_food({"food": "rice", "quantity": "1-2", "unit": "cups"}, "Lunch")
    assert ranged is not None
    assert ranged.quantity is None
    assert "range" in ranged.notes


def test_extract_text_pdf() -> None:
    data = _plan_pdf("Day 1\nBreakfast: eggs\nLunch: chicken\nDinner: fish")
    document = extract_pdf_document(data)
    assert document.method == "text"
    assert "breakfast" in document.document_text.lower()
    assert document.pages[0].page_number == 1


def test_meal_plan_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/import/meal-plan",
        files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 Breakfast eggs")), "application/pdf")},
    )
    assert response.status_code == 401


def test_meal_plan_rejects_non_pdf(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/import/meal-plan",
        headers=_auth(token),
        files={"file": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


def test_meal_plan_rejects_oversized_pdf(client: TestClient, monkeypatch) -> None:
    token = _register(client)
    monkeypatch.setattr(
        "app.services.pdf.meal_plan_service.get_settings",
        lambda: type("S", (), {"ai_max_upload_bytes": 20})(),
    )
    response = client.post(
        "/api/v1/import/meal-plan",
        headers=_auth(token),
        files={"file": ("plan.pdf", BytesIO(b"%PDF" + b"x" * 50), "application/pdf")},
    )
    assert response.status_code == 413


def test_normal_text_and_multi_meal_preview_confirm(client: TestClient) -> None:
    _override(lambda _prompt, _parts: _payload())
    try:
        token = _register(client)
        headers = _auth(token)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=headers,
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 Breakfast eggs Lunch chicken")), "application/pdf")},
        )
        assert preview.status_code == 200, preview.text
        body = preview.json()
        assert body["success"] is True
        assert body["days_detected"] == 1
        assert body["foods_detected"] >= 5
        breakfast = body["days"][0]["meals"]["breakfast"]
        assert breakfast[0]["original_label"] == "Morning meal"
        snack = body["days"][0]["meals"]["morning_snack"][0]
        assert snack["original_label"] == "Mid-morning snack"
        unknown = {
            "document_type": "meal_plan",
            "title": None,
            "days": [
                {
                    "day": 1,
                    "date": None,
                    "meals": {
                        "breakfast": [{"food": "xyzzy-not-a-real-food", "quantity": 1, "unit": "cup"}],
                        "morning_snack": [],
                        "lunch": [],
                        "evening_snack": [],
                        "dinner": [],
                        "other": [],
                    },
                }
            ],
        }
        _override(lambda _prompt, _parts: unknown)
        preview2 = client.post(
            "/api/v1/import/meal-plan",
            headers=headers,
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 Breakfast mystery")), "application/pdf")},
        )
        assert preview2.status_code == 200, preview2.text
        assert preview2.json()["days"][0]["meals"]["breakfast"][0]["nutrition_status"] == "unknown"

        day = body["days"][0]
        foods = []
        for slot, items in day["meals"].items():
            for item in items:
                foods.append(
                    {
                        "food": item["food"],
                        "quantity": item["quantity"],
                        "unit": item["unit"],
                        "notes": item["notes"],
                        "original_label": item["original_label"],
                        "meal_name": item["meal_name"],
                        "alternative": item["alternative"],
                        "nutrition_status": item["nutrition_status"],
                        "calories": item["calories"],
                        "protein": item["protein"],
                        "carbohydrates": item["carbohydrates"],
                        "fat": item["fat"],
                        "fiber": item["fiber"],
                        "sugar": item["sugar"],
                        "slot": slot,
                        "include": True,
                    }
                )
        confirm = client.post(
            "/api/v1/import/meal-plan/confirm",
            headers=headers,
            json={"days": [{"day": 1, "date": day["date"], "include": True, "foods": foods}]},
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["imported_foods"] == len(foods)
        meals = client.get("/api/v1/meals", headers=headers)
        assert meals.json()["total"] >= 1
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_missing_breakfast_and_date_only(client: TestClient) -> None:
    payload = _payload()
    payload["days"][0]["meals"]["breakfast"] = []
    payload["days"][0]["day"] = None
    payload["days"][0]["date"] = "2026-08-16"
    _override(lambda _prompt, _parts: payload)
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("16/08/2026 Lunch chicken")), "application/pdf")},
        )
        assert preview.status_code == 200, preview.text
        day = preview.json()["days"][0]
        assert day["date"] == "2026-08-16"
        assert day["meals"]["breakfast"] == []
        assert day["meals"]["lunch"]
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_multi_day_and_one_day(client: TestClient) -> None:
    payload = _payload()
    payload["days"].append(
        {
            "day": 2,
            "date": None,
            "meals": {
                "breakfast": [{"food": "oatmeal", "quantity": 1, "unit": "bowl"}],
                "morning_snack": [],
                "lunch": [],
                "evening_snack": [],
                "dinner": [],
                "other": [],
            },
        }
    )
    _override(lambda _prompt, _parts: payload)
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 and Day 2 meal plan eggs oatmeal")), "application/pdf")},
        )
        assert preview.status_code == 200, preview.text
        assert preview.json()["days_detected"] == 2
        assert preview.json()["days"][1]["day"] == 2
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_recipe_style_and_table_layout(client: TestClient) -> None:
    payload = {
        "document_type": "meal_plan",
        "title": "Table plan",
        "days": [
            {
                "day": 1,
                "date": None,
                "meals": {
                    "breakfast": [],
                    "morning_snack": [],
                    "lunch": [],
                    "evening_snack": [],
                    "dinner": [
                        {"food": "chicken", "quantity": 4, "unit": "oz", "meal_name": "Chicken and Vegetable Stir-Fry"},
                        {"food": "brown rice", "quantity": 1, "unit": "cup", "meal_name": "Chicken and Vegetable Stir-Fry"},
                        {"food": "broccoli", "quantity": 1, "unit": "cup", "meal_name": "Chicken and Vegetable Stir-Fry"},
                    ],
                    "other": [],
                },
            }
        ],
    }
    _override(lambda _prompt, _parts: payload)
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("plan.pdf", BytesIO(_plan_pdf(CSV)), "application/pdf")},
        )
        assert preview.status_code == 200, preview.text
        dinner = preview.json()["days"][0]["meals"]["dinner"]
        assert len(dinner) == 3
        assert dinner[0]["meal_name"] == "Chicken and Vegetable Stir-Fry"
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_scanned_pdf_uses_ocr_path(client: TestClient, monkeypatch) -> None:
    from app.services.pdf.text_extractor import ExtractedDocument, ExtractedPage

    monkeypatch.setattr(
        "app.services.pdf.meal_plan_service.extract_pdf_document",
        lambda _data: ExtractedDocument(
            document_text="",
            pages=[ExtractedPage(page_number=1, text="", image=b"fake-jpeg")],
            method="ocr",
        ),
    )
    _override(lambda _prompt, _parts: _payload())
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("scan.pdf", BytesIO(_plan_pdf("x")), "application/pdf")},
        )
        assert preview.status_code == 200, preview.text
        assert preview.json()["extraction_method"] == "ocr"
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_malformed_gemini_response(client: TestClient) -> None:
    _override(lambda _prompt, _parts: {"days": "nope"})
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 Breakfast eggs toast lunch")), "application/pdf")},
        )
        assert preview.status_code == 502
        assert preview.json()["error"]["code"] == "AI_INVALID_RESPONSE"
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)


def test_gemini_unavailable(client: TestClient) -> None:
    def boom(_prompt, _parts):
        raise AppError("AI_PROVIDER_ERROR", "AI analysis service is temporarily unavailable. Please try again.", 502)

    _override(boom)
    try:
        token = _register(client)
        preview = client.post(
            "/api/v1/import/meal-plan",
            headers=_auth(token),
            files={"file": ("plan.pdf", BytesIO(_plan_pdf("Day 1 Breakfast eggs toast lunch")), "application/pdf")},
        )
        assert preview.status_code == 502
        assert "image" not in preview.json()["error"]["message"].lower()
    finally:
        app.dependency_overrides.pop(_meal_plan_service, None)
