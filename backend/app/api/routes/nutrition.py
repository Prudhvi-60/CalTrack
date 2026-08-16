from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.nutrition import (
    DailyNutritionResponse,
    GoalComparisonResponse,
    MicronutrientListResponse,
    TrendListResponse,
    WeeklyNutritionResponse,
)
from app.services.nutrition_service import NutritionService

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

_errors = {401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


def _service(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> NutritionService:
    return NutritionService(db, user)


@router.get(
    "/daily",
    response_model=DailyNutritionResponse,
    summary="Daily nutrition",
    description="Totals, remaining macros, today's meals, and recent foods for a UTC calendar day.",
    responses=_errors,
)
def daily_nutrition(
    date: date | None = Query(None, description="UTC day (YYYY-MM-DD). Defaults to today."),
    service: NutritionService = Depends(_service),
) -> DailyNutritionResponse:
    return service.daily(date)


@router.get(
    "/weekly",
    response_model=WeeklyNutritionResponse,
    summary="Weekly nutrition",
    description="Seven UTC days ending on end_date (inclusive), with per-day calorie and macro totals.",
    responses=_errors,
)
def weekly_nutrition(
    end_date: date | None = Query(None, description="Last UTC day of the 7-day window."),
    service: NutritionService = Depends(_service),
) -> WeeklyNutritionResponse:
    return service.weekly(end_date)


@router.get(
    "/trends",
    response_model=TrendListResponse,
    summary="Nutrition trends",
    description="Daily calorie and macro points for the last 7, 30, or 90 UTC days. Paginated.",
    responses=_errors,
)
def nutrition_trends(
    days: int = Query(7, description="Window length. Must be 7, 30, or 90."),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    service: NutritionService = Depends(_service),
) -> TrendListResponse:
    return service.trends(days, page, page_size)


@router.get(
    "/micronutrients",
    response_model=MicronutrientListResponse,
    summary="Micronutrient totals",
    description="Aggregated micronutrients for a UTC date range. Paginated.",
    responses=_errors,
)
def micronutrient_totals(
    days: int | None = Query(None, description="7, 30, or 90. Overrides start_date/end_date when set."),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NutritionService = Depends(_service),
) -> MicronutrientListResponse:
    return service.micronutrients(
        days=days,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/goal-comparison",
    response_model=GoalComparisonResponse,
    summary="Goal vs actual",
    description="Compares intake to calorie and macro targets for one day or a 7/30/90-day window. Period targets are daily goals multiplied by the number of days.",
    responses=_errors,
)
def goal_comparison(
    date: date | None = Query(None, description="UTC day (YYYY-MM-DD). Defaults to today when days is omitted."),
    days: int | None = Query(None, description="7, 30, or 90. When set, compares the full window."),
    service: NutritionService = Depends(_service),
) -> GoalComparisonResponse:
    return service.goal_comparison(date, days)
