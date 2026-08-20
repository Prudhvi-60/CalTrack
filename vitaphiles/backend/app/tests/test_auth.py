from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.core.security import REFRESH_COOKIE_NAME


def _unique() -> str:
    return uuid4().hex[:10]


def _register(
    client: TestClient,
    *,
    email: str | None = None,
    username: str | None = None,
    password: str = "SecurePass1!",
) -> tuple[dict, str]:
    suffix = _unique()
    payload_email = email or f"user-{suffix}@example.com"
    payload_username = username or f"u_{suffix[:8]}"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": payload_email,
            "username": payload_username,
            "display_name": "Test Reader",
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json(), payload_email


def test_register_creates_user_and_returns_token(client: TestClient) -> None:
    body, email = _register(client)
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == email
    assert body["user"]["display_name"] == "Test Reader"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_email(client: TestClient) -> None:
    _, email = _register(client)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"other_{_unique()[:6]}",
            "display_name": "Other",
            "password": "AnotherPass1!",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_EMAIL"


def test_register_duplicate_username(client: TestClient) -> None:
    suffix = _unique()[:8]
    username = f"u_{suffix}"
    _register(client, username=username)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"second-{suffix}@example.com",
            "username": username,
            "display_name": "Other",
            "password": "AnotherPass1!",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_USERNAME"


def test_login_success(client: TestClient) -> None:
    password = "SecurePass1!"
    _, email = _register(client, password=password)
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_login_invalid_password(client: TestClient) -> None:
    _, email = _register(client)
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "SecurePass1!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_invalid_email_is_validation_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "SecurePass1!"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "SecurePass1!" not in response.text


def test_me_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_with_token(client: TestClient) -> None:
    body, email = _register(client)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["username"].startswith("u_")


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_me_rejects_expired_token(client: TestClient) -> None:
    settings = get_settings()
    token = jwt.encode(
        {"sub": "1", "type": "access", "ver": 0, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_user_isolation_tokens(client: TestClient) -> None:
    first, first_email = _register(client)
    second, second_email = _register(client)
    me_first = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    me_second = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert me_first.json()["email"] == first_email
    assert me_second.json()["email"] == second_email
    assert me_first.json()["id"] != me_second.json()["id"]


def test_logout_without_session(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200


def test_logout_authenticated(client: TestClient) -> None:
    body, _ = _register(client)
    token = body["access_token"]
    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user-{_unique()}@example.com",
            "username": f"u_{_unique()[:8]}",
            "display_name": "Test",
            "password": "short",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_profile(client: TestClient) -> None:
    body, _ = _register(client)
    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        json={"display_name": "Updated Name", "bio": "Loves Dune."},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Name"
    assert response.json()["bio"] == "Loves Dune."


def test_change_password(client: TestClient) -> None:
    password = "SecurePass1!"
    body, email = _register(client, password=password)
    token = body["access_token"]
    bad = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrong-password", "new_password": "NewSecure1!"},
    )
    assert bad.status_code == 401
    ok = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": password, "new_password": "NewSecure1!"},
    )
    assert ok.status_code == 200
    stale = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert stale.status_code == 401
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewSecure1!"})
    assert login.status_code == 200


def test_register_sets_refresh_cookie_not_body(client: TestClient) -> None:
    body, _ = _register(client)
    assert "refresh_token" not in body
    assert client.cookies.get(REFRESH_COOKIE_NAME)


def test_refresh_rotates_cookie_and_access_token(client: TestClient) -> None:
    _body, email = _register(client)
    first_refresh = client.cookies.get(REFRESH_COOKIE_NAME)
    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["user"]["email"] == email
    assert client.cookies.get(REFRESH_COOKIE_NAME) != first_refresh
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert me.status_code == 200


def test_refresh_reuse_is_rejected(client: TestClient) -> None:
    _register(client)
    stolen = client.cookies.get(REFRESH_COOKIE_NAME)
    assert stolen
    first = client.post("/api/v1/auth/refresh")
    assert first.status_code == 200
    client.cookies.set(REFRESH_COOKIE_NAME, stolen, path="/api/v1/auth")
    reused = client.post("/api/v1/auth/refresh")
    assert reused.status_code == 401


def test_refresh_without_cookie(client: TestClient) -> None:
    client.cookies.clear()
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
