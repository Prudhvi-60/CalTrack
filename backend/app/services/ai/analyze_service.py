from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import User
from app.schemas.ai import FoodAnalysisResult
from app.services.ai.feedback_service import FeedbackService
from app.services.ai.vision_service import VisionService
from app.utils.images import content_type_kind, reject_if_image_too_large, sniff_image_kind
from sqlalchemy.orm import Session

_MEDIA = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def analyze_image(
    *,
    data: bytes,
    content_type: str | None,
    analysis_type: str,
    vision: VisionService,
    db: Session | None = None,
    user: User | None = None,
) -> FoodAnalysisResult:
    settings = get_settings()
    if analysis_type not in {"food", "label"}:
        raise AppError("VALIDATION_ERROR", "analysis_type must be food or label", 422)
    if not data:
        raise AppError("INVALID_IMAGE", "The uploaded file is empty", 400)
    if len(data) > settings.ai_max_upload_bytes:
        raise AppError("FILE_TOO_LARGE", "Image must be 5 MB or smaller", 413)

    kind = sniff_image_kind(data)
    declared = content_type_kind(content_type)
    if kind is None:
        raise AppError("INVALID_IMAGE", "File is not a valid JPEG, PNG, or WEBP image", 400)
    if declared and declared != kind:
        raise AppError("INVALID_IMAGE", "File type does not match the image contents", 400)
    reject_if_image_too_large(data, kind)

    media_type = _MEDIA[kind]
    if analysis_type == "label":
        result = vision.analyze_nutrition_label(data, media_type)
    else:
        result = vision.analyze_food_image(data, media_type)

    if db is not None and user is not None:
        session = FeedbackService(db, user).start_analysis(
            analysis_type=analysis_type,
            image=data if user.allow_training_data_collection else None,
            kind=kind if user.allow_training_data_collection else None,
        )
        result = result.model_copy(update={"analysis_id": session.id})
    return result
