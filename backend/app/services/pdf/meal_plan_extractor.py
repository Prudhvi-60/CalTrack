from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.schemas.meal_plan import MealPlanDay, MealPlanFood, MealPlanMeals, MealPlanPreviewResponse
from app.services.ai.gemini_client import generate_structured_json
from app.services.pdf.meal_slots import SLOT_KEYS, normalize_slot
from app.services.pdf.text_extractor import ExtractedDocument, ExtractedPage

_PROMPT = (Path(__file__).parent.parent / "ai" / "prompts" / "meal_plan.txt").read_text(encoding="utf-8")
_CHUNK_CHARS = 9000
_IMAGE_BATCH = 3

JsonCompleter = Callable[[str, list[Any]], dict[str, Any]]


class MealPlanExtractor:
    def __init__(
        self,
        settings: Settings | None = None,
        completer: JsonCompleter | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.completer = completer

    def extract(self, document: ExtractedDocument) -> MealPlanPreviewResponse:
        if document.method == "ocr":
            payloads = self._extract_from_images(document.pages)
        else:
            payloads = self._extract_from_text(document.document_text)
        merged = _merge_payloads(payloads)
        days = [_parse_day(item) for item in merged.get("days") or []]
        days = [day for day in days if _day_has_food(day)]
        if not days:
            raise AppError(
                "UNSUPPORTED_DOCUMENT",
                "No meals were found in this PDF. Try a meal plan or food diary.",
                400,
            )
        foods = _count_foods(days)
        meals = _count_meals(days)
        warnings = [
            "Review every day before importing. Nothing is saved until you confirm.",
            "Calories are filled only when a food matches the CalTrack nutrition database.",
        ]
        if document.method == "ocr":
            warnings.append("This looked like a scan. Check names and quantities carefully.")
        return MealPlanPreviewResponse(
            success=True,
            document_type=str(merged.get("document_type") or "meal_plan"),
            title=_optional_str(merged.get("title")),
            extraction_method=document.method,
            days_detected=len(days),
            meals_detected=meals,
            foods_detected=foods,
            warnings=warnings,
            days=days,
        )

    def _complete(self, parts: list[Any]) -> dict[str, Any]:
        if not self.settings.ai_api_key:
            raise AppError(
                "AI_NOT_CONFIGURED",
                "Meal-plan extraction is not configured. Set GEMINI_API_KEY on the FastAPI server.",
                503,
            )
        if self.completer is not None:
            return self.completer(_PROMPT, parts)
        return generate_structured_json(self.settings, _PROMPT, parts)

    def _extract_from_text(self, text: str) -> list[dict[str, Any]]:
        chunks = _chunk_text(text)
        return [self._complete([chunk]) for chunk in chunks]

    def _extract_from_images(self, pages: list[ExtractedPage]) -> list[dict[str, Any]]:
        from google.genai import types

        images = [page for page in pages if page.image]
        if not images:
            raise AppError("OCR_FAILED", "Could not read this scanned PDF.", 400)
        payloads: list[dict[str, Any]] = []
        for start in range(0, len(images), _IMAGE_BATCH):
            batch = images[start : start + _IMAGE_BATCH]
            parts: list[Any] = [
                types.Part.from_text(text="Extract meals from these PDF page images. Return JSON only.")
            ]
            for page in batch:
                parts.append(types.Part.from_bytes(data=page.image, mime_type="image/jpeg"))
            payloads.append(self._complete(parts))
        return payloads


def _chunk_text(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        raise AppError("EMPTY_PDF", "The PDF did not contain readable text.", 400)
    if len(cleaned) <= _CHUNK_CHARS:
        return [cleaned]
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for block in cleaned.split("\n\n"):
        extra = len(block) + 2
        if current and size + extra > _CHUNK_CHARS:
            chunks.append("\n\n".join(current))
            current = [block]
            size = extra
        else:
            current.append(block)
            size += extra
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [cleaned]


def _merge_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    title = None
    document_type = "meal_plan"
    days: list[dict[str, Any]] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            raise AppError("AI_INVALID_RESPONSE", "AI did not return a meal plan object", 502)
        title = title or _optional_str(payload.get("title"))
        document_type = str(payload.get("document_type") or document_type)
        raw_days = payload.get("days") or []
        if not isinstance(raw_days, list):
            raise AppError("AI_INVALID_RESPONSE", "AI meal plan days must be a list", 502)
        days.extend(item for item in raw_days if isinstance(item, dict))
    merged: dict[tuple[object, object], dict[str, Any]] = {}
    order: list[tuple[object, object]] = []
    for item in days:
        key = (item.get("date"), item.get("day"), item.get("label"))
        if key not in merged:
            merged[key] = item
            order.append(key)
        else:
            merged[key] = _merge_day_dicts(merged[key], item)
    return {"document_type": document_type, "title": title, "days": [merged[key] for key in order]}


def _merge_day_dicts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    meals = dict(left.get("meals") or {})
    extra = right.get("meals") or {}
    if isinstance(extra, dict):
        for slot, foods in extra.items():
            existing = list(meals.get(slot) or [])
            if isinstance(foods, list):
                existing.extend(foods)
            meals[slot] = existing
    combined = dict(left)
    combined["meals"] = meals
    return combined


def _parse_day(raw: dict[str, Any]) -> MealPlanDay:
    meals_raw = raw.get("meals") if isinstance(raw.get("meals"), dict) else {}
    slots: dict[str, list[MealPlanFood]] = {key: [] for key in SLOT_KEYS}
    for key, items in meals_raw.items():
        slot = key if key in SLOT_KEYS else normalize_slot(str(key))
        if not isinstance(items, list):
            continue
        for item in items:
            food = _parse_food(item, default_label=str(key))
            if food:
                slots[slot].append(food)
    day_number = raw.get("day")
    parsed_day = None
    if isinstance(day_number, int) and day_number >= 1:
        parsed_day = day_number
    elif isinstance(day_number, str) and day_number.strip().isdigit():
        parsed_day = int(day_number.strip())
    return MealPlanDay(
        day=parsed_day,
        date=_parse_date(raw.get("date")),
        label=_optional_str(raw.get("label")),
        meals=MealPlanMeals(**slots),
    )


def _parse_food(raw: object, default_label: str) -> MealPlanFood | None:
    if isinstance(raw, str):
        name = raw.strip()
        if not name:
            return None
        return MealPlanFood(food=name[:255], original_label=default_label[:80] or None)
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("food") or raw.get("food_name") or raw.get("name") or "").strip()
    if not name:
        return None
    qty_text = raw.get("quantity_text")
    quantity, unit, notes = _parse_amount(raw.get("quantity"), raw.get("unit"), raw.get("notes"))
    alternative = _optional_str(raw.get("alternative"))
    if not alternative and " or " in name.lower():
        parts = [part.strip() for part in name.replace(" OR ", " or ").split(" or ", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            name, alternative = parts[0], parts[1]
    original = _optional_str(raw.get("original_label")) or default_label
    return MealPlanFood(
        food=name[:255],
        quantity=quantity,
        quantity_text=str(qty_text)[:80] if qty_text else None,
        unit=unit,
        notes=notes,
        original_label=original[:80] if original else None,
        meal_name=_optional_str(raw.get("meal_name")),
        alternative=alternative,
    )


def _parse_amount(quantity: object, unit: object, notes: object) -> tuple[Decimal | None, str | None, str]:
    note_text = str(notes or "").strip()
    unit_text = str(unit or "").strip()[:40] or None
    if quantity is None or quantity == "":
        return None, unit_text, note_text
    if isinstance(quantity, (int, float, Decimal)):
        value = Decimal(str(quantity))
        if value < 0:
            return None, unit_text, note_text
        return value, unit_text, note_text
    text = str(quantity).strip()
    if not text:
        return None, unit_text, note_text
    if "-" in text and not text.startswith("-"):
        extra = f"range {text}"
        note_text = f"{note_text}; {extra}".strip("; ") if note_text else extra
        return None, unit_text, note_text
    if "/" in text:
        try:
            left, right = text.split("/", 1)
            value = Decimal(left.strip()) / Decimal(right.strip())
            if value >= 0:
                return value, unit_text, note_text
        except (InvalidOperation, ValueError, ZeroDivisionError):
            extra = text
            note_text = f"{note_text}; {extra}".strip("; ") if note_text else extra
            return None, unit_text, note_text
    try:
        value = Decimal(text.replace(",", ""))
    except InvalidOperation:
        extra = text
        note_text = f"{note_text}; {extra}".strip("; ") if note_text else extra
        return None, unit_text, note_text
    if value < 0:
        return None, unit_text, note_text
    return value, unit_text, note_text


def _parse_date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _day_has_food(day: MealPlanDay) -> bool:
    meals = day.meals
    return any(getattr(meals, key) for key in SLOT_KEYS)


def _count_foods(days: list[MealPlanDay]) -> int:
    total = 0
    for day in days:
        for key in SLOT_KEYS:
            total += len(getattr(day.meals, key))
    return total


def _count_meals(days: list[MealPlanDay]) -> int:
    total = 0
    for day in days:
        for key in SLOT_KEYS:
            if getattr(day.meals, key):
                total += 1
    return total
