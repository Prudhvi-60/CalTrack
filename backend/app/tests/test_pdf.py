from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.services.pdf.pdf_parser import rows_from_table


CSV = (
    "Date,Meal type,Food,Quantity,Unit,Calories,Protein,Carbohydrates,Fat,Fiber,Sugar\n"
    "2026-08-15,Breakfast,Oatmeal,1,bowl,150,5,27,3,4,1\n"
    "2026-08-15,Breakfast,Blueberries,0.5,cup,40,0.5,10,0.2,2,7\n"
    "bad,snack,x,-1,g,abc,0,0,0,0,0\n"
)


def _pdf_from_text(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    commands = ["BT /F1 10 Tf 40 750 Td"]
    for index, line in enumerate(escaped.splitlines()):
        if index:
            commands.append("T*")
        commands.append(f"({line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        b"4 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    return pdf


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"pdf-{uuid4().hex[:12]}@example.com", "name": "PDF User", "password": "SecurePass1!"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_rows_from_table_marks_invalid() -> None:
    table = [line.split(",") for line in CSV.strip().splitlines()]
    rows = rows_from_table(table)
    assert rows[0].valid
    assert rows[1].valid
    assert not rows[2].valid
    assert rows[0].food_name == "Oatmeal"


def test_pdf_preview_and_confirm(client: TestClient, monkeypatch) -> None:
    table = [line.split(",") for line in CSV.strip().splitlines()]
    monkeypatch.setattr("app.services.pdf.pdf_import_service.parse_pdf", lambda _data: table)
    token = _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    preview = client.post(
        "/api/v1/import/pdf",
        headers=headers,
        files={"file": ("diary.pdf", BytesIO(_pdf_from_text(CSV)), "application/pdf")},
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["valid_count"] >= 2
    assert body["invalid_count"] >= 1
    meals_before = client.get("/api/v1/meals", headers=headers)
    assert meals_before.json()["total"] == 0

    valid_rows = [
        {
            "date": row["date"],
            "meal_type": row["meal_type"],
            "food_name": row["food_name"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "calories": row["calories"],
            "protein": row["protein"],
            "carbohydrates": row["carbohydrates"],
            "fat": row["fat"],
            "fiber": row["fiber"],
            "sugar": row["sugar"],
        }
        for row in body["rows"]
        if row["valid"]
    ]
    confirm = client.post("/api/v1/import/pdf/confirm", headers=headers, json={"rows": valid_rows})
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["imported_foods"] == len(valid_rows)
    meals = client.get("/api/v1/meals", headers=headers)
    assert meals.json()["total"] >= 1


def test_pdf_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/import/pdf",
        files={"file": ("diary.pdf", BytesIO(_pdf_from_text(CSV)), "application/pdf")},
    )
    assert response.status_code == 401


def test_pdf_rejects_non_pdf(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/import/pdf",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
