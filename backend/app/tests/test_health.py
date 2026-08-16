from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_ai_does_not_include_a_secret() -> None:
    response = client.get("/api/v1/health/ai")
    assert response.status_code == 200
    body = response.json()
    assert "GEMINI_API_KEY configured" in body
    assert "AI_MODEL configured" in body
    assert isinstance(body["GEMINI_API_KEY configured"], bool)
    assert isinstance(body["AI_MODEL configured"], bool)
    joined = str(body).lower()
    assert "aiza" not in joined
    assert "sk-" not in joined


def test_health_ready_checks_database() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert "password" not in str(body).lower()
    assert "postgresql" not in str(body).lower()


def test_health_root() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_unhandled_errors_do_not_include_traceback() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    body = response.json()
    assert "error" in body
    assert "traceback" not in str(body).lower()


def test_login_validation_error_does_not_echo_credentials() -> None:
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "super-secret-password"})
    assert response.status_code == 422
    text = response.text.lower()
    assert "super-secret-password" not in text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
