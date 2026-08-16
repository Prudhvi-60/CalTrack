from uuid import uuid4

from fastapi.testclient import TestClient

PREFLIGHT_HEADERS = {
    "Origin": "http://localhost:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization,content-type,accept",
}

PREFLIGHT_PATHS = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/ai/analyze-food",
)


def test_register_preflight_allows_localhost_vite(client: TestClient) -> None:
    response = client.options("/api/v1/auth/register", headers=PREFLIGHT_HEADERS)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"
    allowed = response.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allowed
    assert "content-type" in allowed
    assert "accept" in allowed


def test_auth_and_ai_preflight_succeed(client: TestClient) -> None:
    for path in PREFLIGHT_PATHS:
        response = client.options(path, headers=PREFLIGHT_HEADERS)
        assert response.status_code == 200, f"{path} preflight failed: {response.status_code} {response.text}"
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_register_post_succeeds_after_preflight(client: TestClient) -> None:
    origin = "http://localhost:5173"
    preflight = client.options("/api/v1/auth/register", headers=PREFLIGHT_HEADERS)
    assert preflight.status_code == 200

    email = f"cors-{uuid4().hex[:12]}@example.com"
    created = client.post(
        "/api/v1/auth/register",
        headers={"Origin": origin, "Accept": "application/json"},
        json={"email": email, "name": "Cors User", "password": "SecurePass1!"},
    )
    assert created.status_code == 201
    assert created.headers.get("access-control-allow-origin") == origin
    assert created.json()["user"]["email"] == email
