from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import User
from app.schemas.ai import AiCorrectionCreate, AiCorrectionPublic
from app.services.ai.feedback_service import FeedbackService


class CorrectionService:
    """Compatibility wrapper around FeedbackService."""

    def __init__(self, db: Session, user: User) -> None:
        self.inner = FeedbackService(db, user)

    def record(self, payload: AiCorrectionCreate) -> list[AiCorrectionPublic]:
        return self.inner.record(payload)
