from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.meal_plan import MealPlanConfirmRequest, MealPlanConfirmResponse, MealPlanPreviewResponse
from app.schemas.pdf import PdfConfirmRequest, PdfConfirmResponse, PdfPreviewResponse
from app.services.pdf.meal_plan_service import MealPlanService
from app.services.pdf.pdf_import_service import PdfImportService

router = APIRouter(prefix="/import", tags=["import"])

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


def _service(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> PdfImportService:
    return PdfImportService(db, user)


def _meal_plan_service(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> MealPlanService:
    return MealPlanService(db, user)


@router.post(
    "/pdf",
    response_model=PdfPreviewResponse,
    summary="Preview a food-diary PDF",
    description="Extracts and validates table rows. Nothing is saved until /import/pdf/confirm.",
    responses=_errors,
)
async def preview_pdf(
    file: UploadFile = File(..., description="PDF food diary"),
    service: PdfImportService = Depends(_service),
) -> PdfPreviewResponse:
    data = await file.read()
    return service.preview(data)


@router.post(
    "/pdf/confirm",
    response_model=PdfConfirmResponse,
    summary="Import confirmed PDF rows",
    description="Creates meals for the current user from validated preview rows. Re-validates all values.",
    responses=_errors,
)
def confirm_pdf(
    payload: PdfConfirmRequest,
    service: PdfImportService = Depends(_service),
) -> PdfConfirmResponse:
    return service.confirm(payload)


@router.post(
    "/meal-plan",
    response_model=MealPlanPreviewResponse,
    summary="Extract a meal plan or food diary PDF",
    description="Extracts meals with Gemini after PDF text or scan OCR. Nothing is saved until /import/meal-plan/confirm.",
    responses=_errors,
)
async def preview_meal_plan(
    file: UploadFile = File(..., description="PDF meal plan or food diary"),
    service: MealPlanService = Depends(_meal_plan_service),
) -> MealPlanPreviewResponse:
    data = await file.read()
    return service.preview(data, file.filename, file.content_type)


@router.post(
    "/meal-plan/confirm",
    response_model=MealPlanConfirmResponse,
    summary="Save reviewed meal-plan days",
    description="Creates meals for the current user from the reviewed extraction. Re-validates all values.",
    responses=_errors,
)
def confirm_meal_plan(
    payload: MealPlanConfirmRequest,
    service: MealPlanService = Depends(_meal_plan_service),
) -> MealPlanConfirmResponse:
    return service.confirm(payload)

