from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.ai import AiCorrectionCreate, AiCorrectionPublic, FoodAnalysisResult
from app.schemas.common import ErrorResponse
from app.services.ai.analyze_service import analyze_image
from app.services.ai.corrections_service import CorrectionService
from app.services.ai.vision_service import VisionService

router = APIRouter(prefix="/ai", tags=["ai"])

_errors = {
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}


def get_vision_service() -> VisionService:
    return VisionService()


@router.post(
    "/analyze-food",
    response_model=FoodAnalysisResult,
    summary="Analyze a food or nutrition-label image",
    description=(
        "Uploads a JPEG, PNG, or WEBP image. A multimodal model estimates visible foods, "
        "portions, and nutrition in one request. Nutrition-label images use printed label values. "
        "Results are estimates and are never saved automatically."
    ),
    responses=_errors,
)
async def analyze_food(
    file: UploadFile = File(..., description="Food photo or nutrition label image"),
    analysis_type: str = Form("food", description="food or label"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    vision: VisionService = Depends(get_vision_service),
) -> FoodAnalysisResult:
    data = await file.read()
    return analyze_image(
        data=data,
        content_type=file.content_type,
        analysis_type=analysis_type,
        vision=vision,
        db=db,
        user=user,
    )


@router.post(
    "/corrections",
    response_model=list[AiCorrectionPublic],
    summary="Record user corrections to an AI analysis",
    description=(
        "Stores predicted vs corrected food name and portion for later evaluation. "
        "Does not retrain a model. Call this after the user edits and confirms a meal."
    ),
    responses=_errors,
)
def record_corrections(
    payload: AiCorrectionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiCorrectionPublic]:
    return CorrectionService(db, user).record(payload)
