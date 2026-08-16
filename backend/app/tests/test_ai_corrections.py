from uuid import uuid4

from fastapi.testclient import TestClient


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"corr-{uuid4().hex[:12]}@example.com",
            "name": "Correction User",
            "password": "SecurePass1!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_record_ai_corrections(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/ai/corrections",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "analysis_type": "food",
            "items": [
                {
                    "predicted_name": "rice",
                    "predicted_quantity": 1,
                    "predicted_unit": "cup",
                    "corrected_name": "rice",
                    "corrected_quantity": 1.5,
                    "corrected_unit": "cup",
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["predicted_quantity"] == 1
    assert body[0]["corrected_quantity"] == 1.5
    assert body[0]["food"] == "rice"
    assert body[0]["confirmed"] is False
    assert body[0]["include_in_training"] is False


def test_corrections_require_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/corrections",
        json={
            "analysis_type": "food",
            "items": [
                {
                    "predicted_name": "rice",
                    "predicted_quantity": 1,
                    "predicted_unit": "cup",
                    "corrected_name": "rice",
                    "corrected_quantity": 2,
                    "corrected_unit": "cup",
                }
            ],
        },
    )
    assert response.status_code == 401
