from sqlalchemy import inspect, text

from app.db.database import engine
from app.db.session import SessionLocal
from app.models import AiCorrection, FoodEntry, Goal, Meal, Micronutrient, RefreshToken, User


def test_models_are_mapped() -> None:
    tables = {
        User.__tablename__,
        Goal.__tablename__,
        Meal.__tablename__,
        FoodEntry.__tablename__,
        Micronutrient.__tablename__,
        AiCorrection.__tablename__,
        RefreshToken.__tablename__,
    }
    assert tables == {
        "users",
        "goals",
        "meals",
        "food_entries",
        "micronutrients",
        "ai_corrections",
        "refresh_tokens",
    }


def test_database_connectivity() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_expected_tables_exist() -> None:
    inspector = inspect(engine)
    names = set(inspector.get_table_names())
    assert {
        "users",
        "goals",
        "meals",
        "food_entries",
        "micronutrients",
        "ai_corrections",
        "refresh_tokens",
        "ai_analyses",
        "ai_analysis_feedback",
    }.issubset(names)


def test_session_opens() -> None:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    finally:
        db.close()
