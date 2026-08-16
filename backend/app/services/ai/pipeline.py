from decimal import Decimal

from pydantic import ValidationError

from app.core.exceptions import AppError
from app.models.enums import MealType, NutrientName
from app.schemas.ai import AnalyzedFoodItem, FoodAnalysisResult, VisionFoodPhotoResult

_ALLOWED_NUTRIENTS = {item.value for item in NutrientName}
_MEAL_ALIASES = {
    "breakfast": MealType.BREAKFAST,
    "lunch": MealType.LUNCH,
    "dinner": MealType.DINNER,
    "snack": MealType.SNACK,
    "brunch": MealType.BREAKFAST,
}
_ITEM_ALIASES = {
    "protein_g": "protein",
    "carbs_g": "carbohydrates",
    "carbohydrate_g": "carbohydrates",
    "carbohydrates_g": "carbohydrates",
    "fat_g": "fat",
    "fiber_g": "fiber",
    "sugar_g": "sugar",
}


def confidence_level(value: float) -> str:
    if value >= 0.8:
        return "HIGH"
    if value >= 0.55:
        return "MEDIUM"
    return "LOW"


def map_meal_type(value: str | None) -> MealType | None:
    if not value:
        return None
    key = value.strip().lower()
    if key in _MEAL_ALIASES:
        return _MEAL_ALIASES[key]
    upper = value.strip().upper()
    try:
        return MealType(upper)
    except ValueError:
        return None


def is_non_food_payload(raw: dict) -> bool:
    if raw.get("is_food") is False:
        return True
    if str(raw.get("error") or "").lower() in {"not_food", "non_food", "no_food"}:
        return True
    items = raw.get("food_items") if raw.get("food_items") is not None else raw.get("foods")
    if isinstance(items, list) and len(items) == 0 and raw.get("is_food") is False:
        return True
    return False


def _normalize_item(item: dict, overall: float | None) -> dict | None:
    name = str(item.get("name") or "").strip()
    if not name:
        return None
    normalized = dict(item)
    for source, target in _ITEM_ALIASES.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized[source]
    confidence = normalized.get("confidence", overall if overall is not None else 0.5)
    return {
        "name": name,
        "quantity": normalized.get("quantity", 1),
        "unit": normalized.get("unit") or "serving",
        "calories": normalized.get("calories", 0),
        "protein": normalized.get("protein", 0),
        "carbohydrates": normalized.get("carbohydrates", 0),
        "fat": normalized.get("fat", 0),
        "fiber": normalized.get("fiber", 0),
        "sugar": normalized.get("sugar", 0),
        "micronutrients": normalized.get("micronutrients") or [],
        "confidence": confidence,
        "estimated_weight_g": normalized.get("estimated_weight_g"),
    }


def coerce_llm_food_payload(raw: dict) -> dict:
    overall = raw.get("confidence")
    source_items = raw.get("food_items")
    if source_items is None:
        source_items = raw.get("foods") or []
    items = []
    for item in source_items:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_item(item, overall if overall is None else float(overall))
        if normalized:
            items.append(normalized)
    notes = str(raw.get("notes") or "").strip()
    if notes and "estimat" not in notes.lower() and "approximat" not in notes.lower() and "confidence" not in notes.lower():
        notes = f"Estimated. {notes}"
    if not notes:
        notes = "Estimated from the photograph. Portions and nutrition are approximate."
    return {
        "food_items": items,
        "confidence": overall,
        "notes": notes,
        "meal_type": raw.get("meal_type"),
        "is_food": raw.get("is_food", True),
    }


def coerce_label_payload(raw: dict) -> dict:
    if raw.get("is_label") is False:
        raw = {**raw, "food_items": []}
    if "food_items" not in raw and "name" in raw:
        raw = {
            "food_items": [raw],
            "confidence": raw.get("confidence", 0.5),
            "notes": raw.get("notes", ""),
            "serving_size": raw.get("serving_size"),
            "servings_per_container": raw.get("servings_per_container"),
        }
    items = []
    for item in raw.get("food_items") or []:
        if not isinstance(item, dict):
            continue
        micros = []
        for micro in item.get("micronutrients") or []:
            if isinstance(micro, dict) and micro.get("nutrient_name") in _ALLOWED_NUTRIENTS:
                micros.append(micro)
        mapped = _normalize_item(item, raw.get("confidence"))
        if mapped is None:
            continue
        mapped["micronutrients"] = micros
        items.append(mapped)
    raw["food_items"] = items
    return raw


class FoodAnalysisPipeline:
    """Validates multimodal LLM output. Does not look up a nutrition database for photos."""

    def finalize_llm_photo(self, result: FoodAnalysisResult) -> FoodAnalysisResult:
        items = []
        warnings = list(result.warnings)
        confidences: list[float] = []
        for item in result.food_items:
            level = confidence_level(item.confidence)
            items.append(
                item.model_copy(
                    update={
                        "nutrition_source": "llm",
                        "confidence_level": level,
                        "matched_food": None,
                    }
                )
            )
            confidences.append(item.confidence)
        overall = min(confidences) if confidences else result.confidence
        if result.confidence:
            overall = min(overall, result.confidence)
        warnings.append(
            "Nutrition values are multimodal LLM estimates from the photo, not lab measurements. Review every value before saving."
        )
        if overall < 0.55:
            warnings.append("Low confidence estimate. Review every food, quantity, and nutrient value before saving.")
        notes = result.notes.strip() or "Estimated from the visible portion. Nutrition is approximate."
        return result.model_copy(
            update={
                "food_items": items,
                "confidence": overall,
                "notes": notes,
                "meal_type": result.meal_type or map_meal_type(None),
                "warnings": _unique(warnings),
            }
        )

    def finalize_label(self, result: FoodAnalysisResult) -> FoodAnalysisResult:
        items = []
        for item in result.food_items:
            items.append(
                item.model_copy(
                    update={
                        "nutrition_source": "label",
                        "confidence_level": confidence_level(result.confidence),
                        "confidence": result.confidence,
                    }
                )
            )
        warnings = list(result.warnings)
        warnings.append("Values were read from the nutrition label and must be reviewed before saving.")
        if result.confidence < 0.5:
            warnings.append("Low confidence estimate. Review every value before saving.")
        return result.model_copy(update={"food_items": items, "warnings": _unique(warnings)})


def parse_llm_food_result(raw: dict) -> FoodAnalysisResult:
    if is_non_food_payload(raw):
        raise AppError(
            "NOT_FOOD",
            "No food was visible in this image. Try a clearer photo of a meal, or log it manually.",
            422,
        )
    coerced = coerce_llm_food_payload(raw)
    if not coerced["food_items"]:
        raise AppError(
            "NOT_FOOD",
            "No food was visible in this image. Try a clearer photo of a meal, or log it manually.",
            422,
        )
    meal = map_meal_type(coerced.get("meal_type") if isinstance(coerced.get("meal_type"), str) else None)
    overall = coerced.get("confidence")
    try:
        items = [AnalyzedFoodItem.model_validate({**item, "nutrition_source": "llm"}) for item in coerced["food_items"]]
    except ValidationError as exc:
        raise AppError("AI_INVALID_RESPONSE", "AI returned data that failed validation", 502) from exc
    if overall is None:
        overall = min(item.confidence for item in items)
    try:
        overall_f = float(overall)
    except (TypeError, ValueError) as exc:
        raise AppError("AI_INVALID_RESPONSE", "AI returned data that failed validation", 502) from exc
    return FoodAnalysisResult(
        analysis_type="food",
        food_items=items,
        confidence=overall_f,
        notes=coerced["notes"],
        meal_type=meal,
        warnings=[],
    )


def parse_food_identification(raw: dict) -> VisionFoodPhotoResult:
    """Legacy helper for identification-only payloads in older tests."""
    from app.schemas.ai import VisionDetectedFood

    coerced = coerce_llm_food_payload(raw)
    try:
        items = [
            VisionDetectedFood(
                name=item["name"],
                quantity=Decimal(str(item["quantity"])),
                unit=str(item["unit"]),
                confidence=float(item["confidence"]),
            )
            for item in coerced["food_items"]
        ]
        return VisionFoodPhotoResult(
            food_items=items,
            meal_type=coerced.get("meal_type"),
            notes=coerced["notes"],
            confidence=coerced.get("confidence"),
        )
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        raise AppError("AI_INVALID_RESPONSE", "AI returned data that failed validation", 502) from exc


def parse_label_result(raw: dict, analysis_type: str = "label") -> FoodAnalysisResult:
    if raw.get("is_label") is False:
        raise AppError(
            "NOT_FOOD",
            "This image does not appear to be a nutrition label. Choose label mode only for a printed Nutrition Facts panel.",
            422,
        )
    coerced = coerce_label_payload(raw)
    try:
        return FoodAnalysisResult.model_validate({**coerced, "analysis_type": analysis_type})
    except ValidationError as exc:
        raise AppError("AI_INVALID_RESPONSE", "AI returned data that failed validation", 502) from exc


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
