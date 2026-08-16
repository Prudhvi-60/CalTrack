from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.chat import get_chat_completer
from app.main import app


def _register(client: TestClient, name: str = "Chat User") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"chat-{uuid4().hex[:12]}@example.com", "name": name, "password": "SecurePass1!"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class _ReplyCompleter:
    def complete(self, messages, tools):
        return {"role": "assistant", "content": "You logged 0 kcal today."}


class _ToolCompleter:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_today",
                        "type": "function",
                        "function": {"name": "get_today_nutrition", "arguments": "{}"},
                    }
                ],
            }
        return {"role": "assistant", "content": "You have not logged meals today."}


def test_chat_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "What did I eat today?"})
    assert response.status_code == 401


def test_chat_reply(client: TestClient) -> None:
    token = _register(client)
    app.dependency_overrides[get_chat_completer] = lambda: _ReplyCompleter()
    try:
        response = client.post(
            "/api/v1/chat",
            headers=_auth(token),
            json={"message": "What did I eat today?"},
        )
    finally:
        app.dependency_overrides.pop(get_chat_completer, None)
    assert response.status_code == 200, response.text
    assert "logged" in response.json()["reply"].lower()


def test_chat_uses_tools_for_current_user_only(client: TestClient) -> None:
    token_a = _register(client, "User A")
    token_b = _register(client, "User B")
    client.post(
        "/api/v1/meals",
        headers=_auth(token_a),
        json={
            "meal_type": "LUNCH",
            "consumed_at": "2026-08-15T12:00:00Z",
            "notes": None,
            "food_entries": [
                {
                    "food_name": "secret stew",
                    "quantity": 1,
                    "unit": "bowl",
                    "calories": 900,
                    "protein": 40,
                    "carbohydrates": 50,
                    "fat": 30,
                }
            ],
        },
    )
    completer = _ToolCompleter()
    app.dependency_overrides[get_chat_completer] = lambda: completer
    try:
        response = client.post(
            "/api/v1/chat",
            headers=_auth(token_b),
            json={"message": "What did I eat today?"},
        )
    finally:
        app.dependency_overrides.pop(get_chat_completer, None)
    assert response.status_code == 200, response.text
    assert "secret stew" not in response.json()["reply"].lower()
    assert response.json()["tools_used"][0]["name"] == "get_today_nutrition"


def test_chat_rejects_blank_message(client: TestClient) -> None:
    token = _register(client)
    response = client.post("/api/v1/chat", headers=_auth(token), json={"message": "   "})
    assert response.status_code == 422


def test_chat_includes_nutrition_snapshot(client: TestClient) -> None:
    token = _register(client)
    client.post(
        "/api/v1/meals",
        headers=_auth(token),
        json={
            "meal_type": "LUNCH",
            "consumed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "notes": None,
            "food_entries": [
                {
                    "food_name": "rice",
                    "quantity": 1,
                    "unit": "cup",
                    "calories": 205,
                    "protein": 4,
                    "carbohydrates": 45,
                    "fat": 0.5,
                }
            ],
        },
    )

    class CapturingCompleter:
        def __init__(self) -> None:
            self.messages = None

        def complete(self, messages, tools):
            self.messages = messages
            return {"role": "assistant", "content": "You have remaining calories based on your log."}

    completer = CapturingCompleter()
    app.dependency_overrides[get_chat_completer] = lambda: completer
    try:
        response = client.post(
            "/api/v1/chat",
            headers=_auth(token),
            json={"message": "How many calories do I have remaining today?"},
        )
    finally:
        app.dependency_overrides.pop(get_chat_completer, None)
    assert response.status_code == 200, response.text
    systems = [item["content"] for item in completer.messages if item["role"] == "system"]
    snapshot = "\n".join(systems)
    assert "Calories consumed today:" in snapshot
    assert "205" in snapshot
    assert "rice" in snapshot.lower()


def test_chat_create_meal_tool_validates(client: TestClient) -> None:
    token = _register(client)

    class CreateCompleter:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages, tools):
            self.calls += 1
            if self.calls == 1:
                return {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_create",
                            "type": "function",
                            "function": {
                                "name": "create_meal",
                                "arguments": '{"meal_type":"BREAKFAST","consumed_at":"2026-08-15T08:00:00Z","food_entries":[{"food_name":"eggs","quantity":2,"unit":"large","calories":140,"protein":12,"carbohydrates":1,"fat":10}]}',
                            },
                        }
                    ],
                }
            return {"role": "assistant", "content": "Logged 2 eggs for breakfast."}

    app.dependency_overrides[get_chat_completer] = lambda: CreateCompleter()
    try:
        response = client.post(
            "/api/v1/chat",
            headers=_auth(token),
            json={"message": "Log 2 eggs for breakfast."},
        )
    finally:
        app.dependency_overrides.pop(get_chat_completer, None)
    assert response.status_code == 200, response.text
    meals = client.get("/api/v1/meals", headers=_auth(token))
    assert meals.json()["total"] == 1
    assert meals.json()["items"][0]["food_entries"][0]["food_name"] == "eggs"
