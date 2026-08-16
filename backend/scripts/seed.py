"""Development seed: demo user, goals, and ~30 days of meals."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import FoodEntry, Goal, Meal, Micronutrient, User
from app.models.enums import MealType, NutrientName

DEMO_EMAIL = "demo@caltrack.app"
DEMO_PASSWORD = "DemoPass123!"
DEMO_NAME = "Demo User"


def _food(
    name: str,
    quantity: float,
    unit: str,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    fiber: float = 0,
    sugar: float = 0,
    micros: list[tuple[NutrientName, float, str]] | None = None,
) -> FoodEntry:
    entry = FoodEntry(
        food_name=name,
        quantity=Decimal(str(quantity)),
        unit=unit,
        calories=Decimal(str(calories)),
        protein=Decimal(str(protein)),
        carbohydrates=Decimal(str(carbs)),
        fat=Decimal(str(fat)),
        fiber=Decimal(str(fiber)),
        sugar=Decimal(str(sugar)),
    )
    for nutrient, amount, unit_name in micros or []:
        entry.micronutrients.append(
            Micronutrient(
                nutrient_name=nutrient.value,
                amount=Decimal(str(amount)),
                unit=unit_name,
            )
        )
    return entry


def _breakfast() -> list[FoodEntry]:
    return [
        _food(
            "Oatmeal with blueberries",
            1,
            "bowl",
            310,
            11,
            54,
            6,
            8,
            12,
            [
                (NutrientName.IRON, 2.1, "mg"),
                (NutrientName.MAGNESIUM, 58, "mg"),
                (NutrientName.VITAMIN_C, 7, "mg"),
                (NutrientName.POTASSIUM, 220, "mg"),
            ],
        ),
        _food(
            "Greek yogurt",
            170,
            "g",
            120,
            17,
            8,
            0.5,
            0,
            7,
            [(NutrientName.CALCIUM, 180, "mg"), (NutrientName.VITAMIN_B12, 0.6, "µg")],
        ),
    ]


def _lunch() -> list[FoodEntry]:
    return [
        _food(
            "Grilled chicken salad",
            1,
            "plate",
            420,
            38,
            18,
            22,
            5,
            6,
            [
                (NutrientName.VITAMIN_A, 420, "µg"),
                (NutrientName.VITAMIN_C, 32, "mg"),
                (NutrientName.VITAMIN_K, 48, "µg"),
                (NutrientName.IRON, 1.8, "mg"),
                (NutrientName.POTASSIUM, 540, "mg"),
            ],
        ),
        _food("Brown rice", 1, "cup", 215, 5, 45, 1.8, 3.5, 0.4, [(NutrientName.MAGNESIUM, 84, "mg")]),
    ]


def _dinner() -> list[FoodEntry]:
    return [
        _food(
            "Salmon with roasted vegetables",
            1,
            "plate",
            560,
            39,
            28,
            30,
            7,
            8,
            [
                (NutrientName.VITAMIN_D, 11, "µg"),
                (NutrientName.VITAMIN_B12, 4.2, "µg"),
                (NutrientName.POTASSIUM, 780, "mg"),
                (NutrientName.ZINC, 1.1, "mg"),
                (NutrientName.SODIUM, 420, "mg"),
            ],
        ),
    ]


def _snack() -> list[FoodEntry]:
    return [
        _food(
            "Banana and almonds",
            1,
            "serving",
            250,
            6,
            30,
            12,
            4.5,
            14,
            [
                (NutrientName.POTASSIUM, 450, "mg"),
                (NutrientName.VITAMIN_B6, 0.4, "mg"),
                (NutrientName.MAGNESIUM, 48, "mg"),
                (NutrientName.VITAMIN_E, 3.2, "mg"),
            ],
        ),
    ]


MEAL_BUILDERS = {
    MealType.BREAKFAST: (_breakfast, 8),
    MealType.LUNCH: (_lunch, 13),
    MealType.DINNER: (_dinner, 19),
    MealType.SNACK: (_snack, 16),
}


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            name=DEMO_NAME,
        )
        user.goals.append(
            Goal(
                daily_calorie_target=Decimal("2200"),
                protein_target=Decimal("130"),
                carb_target=Decimal("250"),
                fat_target=Decimal("70"),
                weight_goal=Decimal("72"),
            )
        )

        today = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for day_offset in range(30):
            day = today - timedelta(days=day_offset)
            types = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]
            if day_offset % 2 == 0:
                types.append(MealType.SNACK)
            for meal_type in types:
                builder, hour = MEAL_BUILDERS[meal_type]
                meal = Meal(
                    meal_type=meal_type,
                    consumed_at=day.replace(hour=hour),
                    notes="Seeded development meal" if day_offset == 0 else None,
                )
                for entry in builder():
                    meal.food_entries.append(entry)
                user.meals.append(meal)

        db.add(user)
        db.commit()
        print(f"Seeded {DEMO_EMAIL} with {len(user.meals)} meals.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
