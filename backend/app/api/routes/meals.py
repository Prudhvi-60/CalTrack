from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.enums import MealType
from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.meal import MealCreate, MealListResponse, MealPublic, MealUpdate
from app.services.meal_service import MealService

router = APIRouter(prefix="/meals", tags=["meals"])

_errors = {
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def _service(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> MealService:
    return MealService(db, user)


@router.get(
    "",
    response_model=MealListResponse,
    summary="List meals",
    description=(
        "Returns the current user's meals with pagination. "
        "Filter by a single date, a date range, meal type, or food name search. "
        "If `date` is provided it takes precedence over start_date/end_date."
    ),
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_meals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date: date | None = Query(None, description="UTC calendar day (YYYY-MM-DD)"),
    start_date: date | None = Query(None, description="Inclusive UTC start day"),
    end_date: date | None = Query(None, description="Inclusive UTC end day"),
    meal_type: MealType | None = Query(None),
    q: str | None = Query(None, min_length=1, max_length=120, description="Search food names"),
    service: MealService = Depends(_service),
) -> MealListResponse:
    return service.list_meals(
        page=page,
        page_size=page_size,
        meal_type=meal_type,
        on_date=date,
        start_date=start_date,
        end_date=end_date,
        search=q,
    )


@router.post(
    "",
    response_model=MealPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal",
    description="Creates a meal with one or more food entries. Nutrition values cannot be negative.",
    responses=_errors,
)
def create_meal(payload: MealCreate, service: MealService = Depends(_service)) -> MealPublic:
    return service.create(payload)


@router.get(
    "/{meal_id}",
    response_model=MealPublic,
    summary="Get a meal",
    description="Returns a meal owned by the current user.",
    responses=_errors,
)
def get_meal(meal_id: int, service: MealService = Depends(_service)) -> MealPublic:
    return service.get(meal_id)


@router.put(
    "/{meal_id}",
    response_model=MealPublic,
    summary="Replace a meal",
    description="Replaces meal metadata and all food entries.",
    responses=_errors,
)
def replace_meal(meal_id: int, payload: MealUpdate, service: MealService = Depends(_service)) -> MealPublic:
    return service.replace(meal_id, payload)


@router.delete(
    "/{meal_id}",
    response_model=MessageResponse,
    summary="Delete a meal",
    description="Deletes a meal and its food entries.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_meal(meal_id: int, service: MealService = Depends(_service)) -> MessageResponse:
    service.delete(meal_id)
    return MessageResponse(message="Meal deleted")
