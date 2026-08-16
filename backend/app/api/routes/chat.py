from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import ErrorResponse
from app.services.ai.chat_service import ChatCompleter, ChatService, HttpChatCompleter
from app.core.config import get_settings

router = APIRouter(prefix="/chat", tags=["chat"])

_errors = {
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}


def get_chat_completer() -> ChatCompleter:
    return HttpChatCompleter(get_settings())


@router.post(
    "",
    response_model=ChatResponse,
    summary="Nutrition assistant",
    description=(
        "Sends a message to the nutrition assistant. "
        "The model may call validated backend tools for this user only. "
        "It never receives a database connection."
    ),
    responses=_errors,
)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    completer: ChatCompleter = Depends(get_chat_completer),
) -> ChatResponse:
    return ChatService(db, user, completer=completer).ask(payload.message, payload.history)
