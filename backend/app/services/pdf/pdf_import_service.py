from collections import defaultdict
from datetime import datetime, time, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.models import User
from app.schemas.meal import FoodEntryCreate, MealCreate
from app.schemas.pdf import PdfConfirmRequest, PdfConfirmResponse, PdfImportRow, PdfPreviewResponse
from app.services.meal_service import MealService
from app.services.pdf.pdf_parser import parse_pdf, rows_from_table


class PdfImportService:
    def __init__(self, db: Session, user: User) -> None:
        self.user = user
        self.meals = MealService(db, user)

    def preview(self, data: bytes) -> PdfPreviewResponse:
        settings = get_settings()
        if not data:
            raise AppError("INVALID_PDF", "The uploaded file is empty", 400)
        if len(data) > settings.ai_max_upload_bytes:
            raise AppError("FILE_TOO_LARGE", "PDF must be 5 MB or smaller", 413)
        table = parse_pdf(data)
        rows = rows_from_table(table)
        if not rows:
            raise AppError("INVALID_PDF", "No table rows were found in the PDF", 400)
        valid = sum(1 for row in rows if row.valid)
        warnings = []
        if valid == 0:
            warnings.append("No valid rows. Fix the table headers and nutrition values, then upload again.")
        warnings.append("Review every row. Nothing is saved until you confirm.")
        return PdfPreviewResponse(
            rows=rows,
            valid_count=valid,
            invalid_count=len(rows) - valid,
            warnings=warnings,
        )

    def confirm(self, payload: PdfConfirmRequest) -> PdfConfirmResponse:
        grouped: dict[tuple, list[PdfImportRow]] = defaultdict(list)
        for row in payload.rows:
            grouped[(row.date, row.meal_type)].append(row)
        created = []
        foods = 0
        for (day, meal_type), items in grouped.items():
            consumed_at = datetime.combine(day, time(12, 0), tzinfo=timezone.utc)
            meal = self.meals.create(
                MealCreate(
                    meal_type=meal_type,
                    consumed_at=consumed_at,
                    notes="Imported from PDF",
                    food_entries=[
                        FoodEntryCreate(
                            food_name=item.food_name,
                            quantity=item.quantity,
                            unit=item.unit,
                            calories=item.calories,
                            protein=item.protein,
                            carbohydrates=item.carbohydrates,
                            fat=item.fat,
                            fiber=item.fiber,
                            sugar=item.sugar,
                        )
                        for item in items
                    ],
                )
            )
            created.append(meal)
            foods += len(items)
        return PdfConfirmResponse(imported_meals=len(created), imported_foods=foods, meals=created)
