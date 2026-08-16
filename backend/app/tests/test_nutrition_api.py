from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

MEAL = {
    "meal_type": "BREAKFAST",
    "consumed_at": datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0).isoformat(),
    "notes": None,
    "food_entries": [
        {
            "food_name": "Oatmeal",
            "quantity": 1,
            "unit": "bowl",
            "calories": 310,
            "protein": 11,
            "carbohydrates": 54,
            "fat": 6,
            "fiber": 8,
            "sugar": 12,
            "micronutrients": [{"nutrient_name": "Iron", "amount": 2.1, "unit": "mg"}],
        }
    ],
}

GOAL = {
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
            "email": f"nutrition-{uuid4().hex[:12]}@example.com",
            "name": "Nutrition User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_nutrition_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/nutrition/daily").status_code == 401


def test_daily_weekly_and_goal_comparison(client: TestClient) -> None:
    token = _register(client)["access_token"]
    headers = _auth(token)
    client.post("/api/v1/goals", json=GOAL, headers=headers)
    created = client.post("/api/v1/meals", json=MEAL, headers=headers)
    assert created.status_code == 201, created.text

    daily = client.get("/api/v1/nutrition/daily", headers=headers)
    assert daily.status_code == 200
    body = daily.json()
    assert body["totals"]["calories"] == 310
    assert body["remaining"]["calories"] == 1890
    assert len(body["meals"]) == 1
    assert body["recent_foods"][0]["food_name"] == "Oatmeal"

    weekly = client.get("/api/v1/nutrition/weekly", headers=headers)
    assert weekly.status_code == 200
    assert len(weekly.json()["days"]) == 7
    assert weekly.json()["totals"]["calories"] == 310

    comparison = client.get("/api/v1/nutrition/goal-comparison", headers=headers)
    assert comparison.status_code == 200
    calories = next(item for item in comparison.json()["items"] if item["name"] == "calories")
    assert comparison.json()["has_goals"] is True
    assert calories["actual"] == 310
    assert calories["target"] == 2200
    assert comparison.json()["days"] == 1


def test_period_reports(client: TestClient) -> None:
    token = _register(client)["access_token"]
    headers = _auth(token)
    client.post("/api/v1/goals", json=GOAL, headers=headers)
    client.post("/api/v1/meals", json=MEAL, headers=headers)

    trends = client.get("/api/v1/nutrition/trends?days=30&page=1&page_size=30", headers=headers)
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["total"] == 30
    assert len(payload["items"]) == 30
    assert payload["totals"]["calories"] == 310

    comparison = client.get("/api/v1/nutrition/goal-comparison?days=7", headers=headers)
    assert comparison.status_code == 200
    calories = next(item for item in comparison.json()["items"] if item["name"] == "calories")
    assert comparison.json()["days"] == 7
    assert calories["actual"] == 310
    assert calories["target"] == 15400

    micros = client.get("/api/v1/nutrition/micronutrients?days=30&page=1&page_size=20", headers=headers)
    assert micros.status_code == 200
    names = {item["nutrient_name"] for item in micros.json()["items"]}
    assert "Iron" in names


def test_trends_and_micronutrients_pagination(client: TestClient) -> None:
    token = _register(client)["access_token"]
    headers = _auth(token)
    client.post("/api/v1/meals", json=MEAL, headers=headers)

    trends = client.get("/api/v1/nutrition/trends?days=7&page=1&page_size=7", headers=headers)
    assert trends.status_code == 200
    payload = trends.json()
    assert payload["total"] == 7
    assert payload["page"] == 1
    assert len(payload["items"]) == 7
    assert payload["totals"]["calories"] == 310

    invalid = client.get("/api/v1/nutrition/trends?days=14", headers=headers)
    assert invalid.status_code == 422

    micros = client.get("/api/v1/nutrition/micronutrients?page=1&page_size=20", headers=headers)
    assert micros.status_code == 200
    names = {item["nutrient_name"] for item in micros.json()["items"]}
    assert "Iron" in names


def test_nutrition_user_isolation(client: TestClient) -> None:
    first = _register(client)
    second = _register(client)
    client.post("/api/v1/meals", json=MEAL, headers=_auth(first["access_token"]))
    other = client.get("/api/v1/nutrition/daily", headers=_auth(second["access_token"]))
    assert other.json()["totals"]["calories"] == 0
    assert other.json()["meals"] == []
