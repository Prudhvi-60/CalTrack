from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "vitaphiles-api"


def test_health_under_api_prefix(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_route_is_enveloped(client: TestClient) -> None:
    response = client.get("/no-such-route")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_orm_models_import() -> None:
    from app.models import Book, Follow, Movie, Review, User, UserBook, UserList, UserMovie

    assert User.__tablename__ == "users"
    assert Book.__tablename__ == "books"
    assert Movie.__tablename__ == "movies"
    assert UserBook.__tablename__ == "user_books"
    assert UserMovie.__tablename__ == "user_movies"
    assert Review.__tablename__ == "reviews"
    assert Follow.__tablename__ == "follows"
    assert UserList.__tablename__ == "lists"
