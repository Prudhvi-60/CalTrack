from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.dependencies import client_ip, get_current_user, get_current_user_optional
from app.core.exceptions import AppError
from app.core.security import REFRESH_COOKIE_NAME
from app.db.session import get_db
from app.models import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.user import UserCreate, UserPublic, UserUpdate
from app.services.auth_service import AuthService, to_user_public

router = APIRouter(prefix="/auth", tags=["auth"])

_error = {
    401: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}


def _attach_refresh(response: Response, raw: str) -> None:
    set_refresh_cookie(response, raw, get_settings())


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register",
    description="Creates an account, sets an HttpOnly refresh cookie, and returns a short-lived access token.",
    responses=_error,
)
def register(
    payload: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    tokens, raw = AuthService(db).register(
        payload,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _attach_refresh(response, raw)
    return tokens


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in",
    responses=_error,
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    tokens, raw = AuthService(db).login(
        payload.email,
        payload.password,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _attach_refresh(response, raw)
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses=_error,
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw:
        raise AppError("UNAUTHORIZED", "Invalid or expired session", 401)
    tokens, new_raw = AuthService(db).refresh(
        raw,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _attach_refresh(response, new_raw)
    return tokens


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Current user",
    responses={401: {"model": ErrorResponse}},
)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return to_user_public(current_user)


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update profile",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    user = AuthService(db).update_profile(current_user, payload)
    return to_user_public(user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    AuthService(db).change_password(current_user, payload)
    return MessageResponse(message="Password updated")


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Sign out",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> MessageResponse:
    raw = request.cookies.get(REFRESH_COOKIE_NAME)
    AuthService(db).logout(current_user, raw)
    clear_refresh_cookie(response, get_settings())
    return MessageResponse(message="Logged out")
