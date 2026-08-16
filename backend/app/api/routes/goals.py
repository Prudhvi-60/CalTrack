from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.goal import GoalCreate, GoalListResponse, GoalPatch, GoalPublic, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])

_auth_errors = {
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def _service(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> GoalService:
    return GoalService(db, user)


@router.get(
    "",
    response_model=GoalListResponse,
    summary="List goals",
    description=(
        "Returns the authenticated user's goals with today's intake and remaining macros. "
        "Pagination is supported even though each user has at most one goal row."
    ),
    responses={401: {"model": ErrorResponse}},
)
def list_goals(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: GoalService = Depends(_service),
) -> GoalListResponse:
    return service.list_goals(page, page_size)


@router.post(
    "",
    response_model=GoalPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create goals",
    description="Sets daily calorie and macro targets. Negative values are rejected.",
    responses=_auth_errors,
)
def create_goals(payload: GoalCreate, service: GoalService = Depends(_service)) -> GoalPublic:
    return service.create(payload)


@router.put(
    "",
    response_model=GoalPublic,
    summary="Replace goals",
    description="Replaces all goal fields for the current user.",
    responses=_auth_errors,
)
def replace_goals(payload: GoalUpdate, service: GoalService = Depends(_service)) -> GoalPublic:
    return service.replace(payload)


@router.patch(
    "",
    response_model=GoalPublic,
    summary="Update goals",
    description="Partially updates goal fields. At least one field is required.",
    responses=_auth_errors,
)
def patch_goals(payload: GoalPatch, service: GoalService = Depends(_service)) -> GoalPublic:
    return service.patch(payload)


@router.delete(
    "",
    response_model=MessageResponse,
    summary="Delete goals",
    description="Removes the current user's goals.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_goals(service: GoalService = Depends(_service)) -> MessageResponse:
    service.delete()
    return MessageResponse(message="Goals deleted")
