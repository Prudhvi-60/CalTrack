from app.models.enums import MealType

SLOT_KEYS = ("breakfast", "morning_snack", "lunch", "evening_snack", "dinner", "other")

_SLOT_ALIASES = {
    "breakfast": "breakfast",
    "morning meal": "breakfast",
    "am meal": "breakfast",
    "morning snack": "morning_snack",
    "mid-morning snack": "morning_snack",
    "mid morning snack": "morning_snack",
    "am snack": "morning_snack",
    "lunch": "lunch",
    "midday meal": "lunch",
    "mid-day meal": "lunch",
    "evening snack": "evening_snack",
    "afternoon snack": "evening_snack",
    "pm snack": "evening_snack",
    "tea time": "evening_snack",
    "teatime": "evening_snack",
    "dinner": "dinner",
    "evening meal": "dinner",
    "supper": "dinner",
    "dessert": "other",
    "pre-workout": "other",
    "pre workout": "other",
    "post-workout": "other",
    "post workout": "other",
    "late-night snack": "other",
    "late night snack": "other",
    "snack": "other",
    "other": "other",
}

_SLOT_TO_MEAL = {
    "breakfast": MealType.BREAKFAST,
    "morning_snack": MealType.SNACK,
    "lunch": MealType.LUNCH,
    "evening_snack": MealType.SNACK,
    "dinner": MealType.DINNER,
    "other": MealType.SNACK,
}

_SLOT_TIMES = {
    "breakfast": (8, 0),
    "morning_snack": (10, 30),
    "lunch": (12, 30),
    "evening_snack": (16, 0),
    "dinner": (19, 0),
    "other": (21, 0),
}

_SLOT_LABELS = {
    "breakfast": "Breakfast",
    "morning_snack": "Morning snack",
    "lunch": "Lunch",
    "evening_snack": "Evening snack",
    "dinner": "Dinner",
    "other": "Other",
}


def normalize_slot(label: str | None) -> str:
    key = " ".join((label or "").strip().lower().replace("_", " ").split())
    return _SLOT_ALIASES.get(key, "other")


def slot_to_meal_type(slot: str) -> MealType:
    return _SLOT_TO_MEAL.get(slot, MealType.SNACK)


def slot_clock(slot: str) -> tuple[int, int]:
    return _SLOT_TIMES.get(slot, (12, 0))


def slot_label(slot: str) -> str:
    return _SLOT_LABELS.get(slot, "Other")
