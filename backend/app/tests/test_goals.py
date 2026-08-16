from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import FoodEntry, Meal
from app.models.enums import MealType

GOAL_PAYLOAD = {
    "daily_calorie_target": 2200,
    "protein_target": 130,
    "carb_target": 250,
    "fat_target": 70,
    "weight_goal": 72,
}


def _register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"goals-{uuid4().hex[:12]}@example.com",
            "name": "Goal User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_goals_require_auth(client: TestClient) -> None:
    response = client.get("/api/v1/goals")
    assert response.status_code == 401


def test_create_and_list_goals(client: TestClient) -> None:
    token = _register(client)["access_token"]
    created = client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    assert created.status_code == 201
    body = created.json()
    assert body["daily_calorie_target"] == 2200
    assert body["calories_actual"] == 0
    assert body["calories_remaining"] == 2200

    listed = client.get("/api/v1/goals?page=1&page_size=20", headers=_auth(token))
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 1
    assert len(payload["items"]) == 1


def test_duplicate_goals_rejected(client: TestClient) -> None:
    token = _register(client)["access_token"]
    assert client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token)).status_code == 201
    again = client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "GOAL_EXISTS"


def test_negative_targets_rejected(client: TestClient) -> None:
    token = _register(client)["access_token"]
    response = client.post(
        "/api/v1/goals",
        json={**GOAL_PAYLOAD, "daily_calorie_target": -1},
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_put_and_patch_goals(client: TestClient) -> None:
    token = _register(client)["access_token"]
    client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    replaced = client.put(
        "/api/v1/goals",
        json={**GOAL_PAYLOAD, "daily_calorie_target": 2000, "weight_goal": None},
        headers=_auth(token),
    )
    assert replaced.status_code == 200
    assert replaced.json()["daily_calorie_target"] == 2000
    assert replaced.json()["weight_goal"] is None

    patched = client.patch("/api/v1/goals", json={"protein_target": 140}, headers=_auth(token))
    assert patched.status_code == 200
    assert patched.json()["protein_target"] == 140
    assert patched.json()["daily_calorie_target"] == 2000


def test_patch_empty_body_rejected(client: TestClient) -> None:
    token = _register(client)["access_token"]
    client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    response = client.patch("/api/v1/goals", json={}, headers=_auth(token))
    assert response.status_code == 422


def test_delete_goals(client: TestClient) -> None:
    token = _register(client)["access_token"]
    client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    deleted = client.delete("/api/v1/goals", headers=_auth(token))
    assert deleted.status_code == 200
    listed = client.get("/api/v1/goals", headers=_auth(token))
    assert listed.json()["total"] == 0
    missing = client.put("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_goal_user_isolation(client: TestClient) -> None:
    first = _register(client)
    second = _register(client)
    client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(first["access_token"]))
    other_list = client.get("/api/v1/goals", headers=_auth(second["access_token"]))
    assert other_list.json()["total"] == 0
    other_put = client.put(
        "/api/v1/goals",
        json=GOAL_PAYLOAD,
        headers=_auth(second["access_token"]),
    )
    assert other_put.status_code == 404


def test_goal_progress_uses_todays_meals(client: TestClient, db_session: Session) -> None:
    registered = _register(client)
    token = registered["access_token"]
    user_id = registered["user"]["id"]
    client.post("/api/v1/goals", json=GOAL_PAYLOAD, headers=_auth(token))

    meal = Meal(
        user_id=user_id,
        meal_type=MealType.BREAKFAST,
        consumed_at=datetime.now(timezone.utc),
    )
    meal.food_entries.append(
        FoodEntry(
            food_name="Eggs",
            quantity=Decimal("2"),
            unit="count",
            calories=Decimal("140"),
            protein=Decimal("12"),
            carbohydrates=Decimal("1"),
            fat=Decimal("10"),
            fiber=Decimal("0"),
            sugar=Decimal("0"),
        )
    )
    db_session.add(meal)
    db_session.flush()

    listed = client.get("/api/v1/goals", headers=_auth(token))
    item = listed.json()["items"][0]
    assert item["calories_actual"] == 140
    assert item["protein_actual"] == 12
    assert item["calories_remaining"] == 2060
