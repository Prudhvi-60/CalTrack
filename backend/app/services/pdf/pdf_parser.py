from __future__ import annotations

from datetime import date as Date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from app.core.exceptions import AppError
from app.models.enums import MealType
from app.schemas.pdf import PdfPreviewRow

_ALIASES = {
    "date": "date",
    "day": "date",
    "meal": "meal_type",
    "meal type": "meal_type",
    "meal_type": "meal_type",
    "food": "food_name",
    "food name": "food_name",
    "food_name": "food_name",
    "qty": "quantity",
    "quantity": "quantity",
    "unit": "unit",
    "kcal": "calories",
    "calories": "calories",
    "protein": "protein",
    "carbs": "carbohydrates",
    "carbohydrates": "carbohydrates",
    "fat": "fat",
    "fiber": "fiber",
    "sugar": "sugar",
}

_MEAL_ALIASES = {
    "breakfast": MealType.BREAKFAST,
    "lunch": MealType.LUNCH,
    "dinner": MealType.DINNER,
    "snack": MealType.SNACK,
}


def parse_pdf(data: bytes) -> list[list[str]]:
    if not data.startswith(b"%PDF"):
        raise AppError("INVALID_PDF", "File is not a valid PDF", 400)
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            tables: list[list[str]] = []
            for page in pdf.pages:
                extracted = page.extract_tables() or []
                for table in extracted:
                    for row in table:
                        tables.append([("" if cell is None else str(cell)).strip() for cell in row])
            if tables and _header_row(tables) is not None:
                return tables
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("INVALID_PDF", "Could not read the PDF", 400) from exc
    return [line.split(",") for line in text.splitlines() if line.strip()]


def rows_from_table(table: list[list[str]]) -> list[PdfPreviewRow]:
    if not table:
        return []
    header_index = _header_row(table)
    mapping = _column_map(table[header_index]) if header_index is not None else {}
    start = header_index + 1 if header_index is not None else 0
    preview: list[PdfPreviewRow] = []
    for offset, raw in enumerate(table[start:], start=start):
        if not any(cell.strip() for cell in raw):
            continue
        preview.append(_parse_row(offset, raw, mapping))
    return preview


def _header_row(table: list[list[str]]) -> int | None:
    for index, row in enumerate(table[:5]):
        names = {_ALIASES.get(cell.strip().lower()) for cell in row}
        if "food_name" in names or "calories" in names:
            return index
    return None


def _column_map(header: list[str]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for index, cell in enumerate(header):
        key = _ALIASES.get(cell.strip().lower())
        if key:
            mapping[index] = key
    return mapping


def _parse_row(index: int, raw: list[str], mapping: dict[int, str]) -> PdfPreviewRow:
    values: dict[str, str] = {}
    if mapping:
        for col, key in mapping.items():
            if col < len(raw):
                values[key] = raw[col].strip()
    elif len(raw) >= 11:
        keys = [
            "date",
            "meal_type",
            "food_name",
            "quantity",
            "unit",
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "fiber",
            "sugar",
        ]
        values = {key: raw[i].strip() for i, key in enumerate(keys)}
    errors: list[str] = []
    parsed: dict[str, object] = {}

    day = _parse_date(values.get("date", ""))
    if day is None:
        errors.append("date is required (YYYY-MM-DD)")
    else:
        parsed["date"] = day

    meal = _parse_meal(values.get("meal_type", ""))
    if meal is None:
        errors.append("meal_type must be breakfast, lunch, dinner, or snack")
    else:
        parsed["meal_type"] = meal

    food = values.get("food_name", "").strip()
    if not food:
        errors.append("food_name is required")
    else:
        parsed["food_name"] = food[:255]

    unit = values.get("unit", "").strip() or "serving"
    parsed["unit"] = unit[:40]

    for field in ("quantity", "calories", "protein", "carbohydrates", "fat", "fiber", "sugar"):
        number = _parse_decimal(values.get(field, "0" if field in {"fiber", "sugar"} else ""))
        if number is None:
            errors.append(f"{field} must be a number 0 or greater")
        else:
            parsed[field] = number

    return PdfPreviewRow(index=index, valid=not errors, errors=errors, **parsed)  # type: ignore[arg-type]


def _parse_date(value: str) -> Date | None:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_meal(value: str) -> MealType | None:
    return _MEAL_ALIASES.get(value.strip().lower())


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = value.strip().replace(",", "")
    if cleaned == "":
        return None
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None
    if number < 0:
        return None
    return number
