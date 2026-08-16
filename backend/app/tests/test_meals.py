from uuid import uuid4

from fastapi.testclient import TestClient

MEAL_BODY = {
    "meal_type": "BREAKFAST",
    "consumed_at": "2026-08-10T08:00:00+00:00",
    "notes": "Test breakfast",
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
            "micronutrients": [
                {"nutrient_name": "Iron", "amount": 2.1, "unit": "mg"},
            ],
        }
    ],
}


def _register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"meals-{uuid4().hex[:12]}@example.com",
            "name": "Meal User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_meals_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/meals").status_code == 401


def test_create_list_and_get_meal(client: TestClient) -> None:
    token = _register(client)["access_token"]
    created = client.post("/api/v1/meals", json=MEAL_BODY, headers=_auth(token))
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["meal_type"] == "BREAKFAST"
    assert body["totals"]["calories"] == 310
    assert body["food_entries"][0]["micronutrients"][0]["nutrient_name"] == "Iron"

    listed = client.get("/api/v1/meals?page=1&page_size=20", headers=_auth(token))
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["total_pages"] == 1
    meal_id = body["id"]
    detail = client.get(f"/api/v1/meals/{meal_id}", headers=_auth(token))
    assert detail.status_code == 200
    assert detail.json()["notes"] == "Test breakfast"


def test_negative_nutrition_rejected(client: TestClient) -> None:
    token = _register(client)["access_token"]
    payload = {
        **MEAL_BODY,
        "food_entries": [{**MEAL_BODY["food_entries"][0], "calories": -5}],
    }
    response = client.post("/api/v1/meals", json=payload, headers=_auth(token))
    assert response.status_code == 422


def test_empty_food_entries_rejected(client: TestClient) -> None:
    token = _register(client)["access_token"]
    response = client.post(
        "/api/v1/meals",
        json={**MEAL_BODY, "food_entries": []},
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_replace_and_delete_meal(client: TestClient) -> None:
    token = _register(client)["access_token"]
    meal_id = client.post("/api/v1/meals", json=MEAL_BODY, headers=_auth(token)).json()["id"]
    updated = client.put(
        f"/api/v1/meals/{meal_id}",
        json={
            **MEAL_BODY,
            "meal_type": "LUNCH",
            "notes": "Updated",
            "food_entries": [
                {
                    "food_name": "Salad",
                    "quantity": 1,
                    "unit": "plate",
                    "calories": 420,
                    "protein": 38,
                    "carbohydrates": 18,
                    "fat": 22,
                }
            ],
        },
        headers=_auth(token),
    )
    assert updated.status_code == 200
    assert updated.json()["meal_type"] == "LUNCH"
    assert updated.json()["totals"]["calories"] == 420
    assert len(updated.json()["food_entries"]) == 1

    deleted = client.delete(f"/api/v1/meals/{meal_id}", headers=_auth(token))
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/meals/{meal_id}", headers=_auth(token)).status_code == 404


def test_meal_filters_and_pagination(client: TestClient) -> None:
    token = _register(client)["access_token"]
    headers = _auth(token)
    breakfast = {**MEAL_BODY, "consumed_at": "2026-08-01T08:00:00+00:00"}
    lunch = {
        **MEAL_BODY,
        "meal_type": "LUNCH",
        "consumed_at": "2026-08-15T13:00:00+00:00",
        "food_entries": [{**MEAL_BODY["food_entries"][0], "food_name": "Chicken salad"}],
    }
    client.post("/api/v1/meals", json=breakfast, headers=headers)
    client.post("/api/v1/meals", json=lunch, headers=headers)

    by_type = client.get("/api/v1/meals?meal_type=BREAKFAST", headers=headers)
    assert by_type.json()["total"] == 1
    assert by_type.json()["items"][0]["meal_type"] == "BREAKFAST"

    by_date = client.get("/api/v1/meals?date=2026-08-15", headers=headers)
    assert by_date.json()["total"] == 1
    assert by_date.json()["items"][0]["meal_type"] == "LUNCH"

    by_range = client.get(
        "/api/v1/meals?start_date=2026-08-01&end_date=2026-08-15&meal_type=BREAKFAST",
        headers=headers,
    )
    assert by_range.json()["total"] == 1

    searched = client.get("/api/v1/meals?q=chicken", headers=headers)
    assert searched.json()["total"] == 1

    page1 = client.get("/api/v1/meals?page=1&page_size=1", headers=headers)
    page2 = client.get("/api/v1/meals?page=2&page_size=1", headers=headers)
    assert page1.json()["total"] == 2
    assert page1.json()["total_pages"] == 2
    assert len(page1.json()["items"]) == 1
    assert len(page2.json()["items"]) == 1
    assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]


def test_dinner_snack_and_multiple_foods(client: TestClient) -> None:
    token = _register(client)["access_token"]
    headers = _auth(token)
    dinner = {
        **MEAL_BODY,
        "meal_type": "DINNER",
        "consumed_at": "2026-08-10T19:00:00+00:00",
        "food_entries": [
            {**MEAL_BODY["food_entries"][0], "food_name": "Salmon", "calories": 280, "protein": 30, "carbohydrates": 0, "fat": 18},
            {
                "food_name": "Rice",
                "quantity": 1,
                "unit": "cup",
                "calories": 205,
                "protein": 4,
                "carbohydrates": 45,
                "fat": 0.5,
            },
        ],
    }
    snack = {
        **MEAL_BODY,
        "meal_type": "SNACK",
        "consumed_at": "2026-08-10T16:00:00+00:00",
        "food_entries": [{**MEAL_BODY["food_entries"][0], "food_name": "Yogurt", "calories": 120}],
    }
    created_dinner = client.post("/api/v1/meals", json=dinner, headers=headers)
    created_snack = client.post("/api/v1/meals", json=snack, headers=headers)
    assert created_dinner.status_code == 201
    assert created_dinner.json()["totals"]["calories"] == 485
    assert len(created_dinner.json()["food_entries"]) == 2
    assert created_snack.status_code == 201
    listed = client.get("/api/v1/meals?meal_type=SNACK", headers=headers)
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["meal_type"] == "SNACK"


def test_invalid_date_range(client: TestClient) -> None:
    token = _register(client)["access_token"]
    response = client.get(
        "/api/v1/meals?start_date=2026-08-15&end_date=2026-08-01",
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_meal_user_isolation(client: TestClient) -> None:
    first = _register(client)
    second = _register(client)
    meal_id = client.post("/api/v1/meals", json=MEAL_BODY, headers=_auth(first["access_token"])).json()["id"]
    other = _auth(second["access_token"])
    assert client.get(f"/api/v1/meals/{meal_id}", headers=other).status_code == 404
    assert client.put(f"/api/v1/meals/{meal_id}", json=MEAL_BODY, headers=other).status_code == 404
    assert client.delete(f"/api/v1/meals/{meal_id}", headers=other).status_code == 404
    assert client.get("/api/v1/meals", headers=other).json()["total"] == 0
