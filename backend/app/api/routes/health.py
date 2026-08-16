from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Process liveness. Use /health/ready to verify PostgreSQL.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health/ai",
    summary="AI configuration check",
    description="Reports whether the Gemini key and model are set. Never returns the key.",
)
def health_ai() -> dict[str, object]:
    settings = get_settings()
    return {
        "provider": "Gemini",
        "GEMINI_API_KEY configured": settings.ai_configured,
        "AI_MODEL configured": bool(settings.ai_model.strip()),
        "AI_MODEL": settings.ai_model,
    }


@router.get(
    "/health/db",
    summary="Database health check",
    description="Runs SELECT 1 against PostgreSQL.",
)
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Verifies the API process and PostgreSQL are available.",
)
def health_ready(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
