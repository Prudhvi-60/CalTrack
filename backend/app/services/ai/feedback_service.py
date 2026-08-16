from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AiAnalysis, AiAnalysisFeedback, User
from app.schemas.ai import AiCorrectionCreate, AiCorrectionPublic


def store_analysis_image(data: bytes, kind: str) -> str | None:
    settings = get_settings()
    if settings.is_production and not settings.training_data_dir:
        return None
    folder = settings.resolved_training_data_dir() / "raw" / "images"
    folder.mkdir(parents=True, exist_ok=True)
    reference = uuid4().hex
    path = folder / f"{reference}.{kind}"
    path.write_bytes(data)
    return f"{reference}.{kind}"


class FeedbackService:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user

    def start_analysis(self, *, analysis_type: str, image: bytes | None, kind: str | None) -> AiAnalysis:
        image_reference = None
        if self.user.allow_training_data_collection and image and kind:
            image_reference = store_analysis_image(image, kind)
        row = AiAnalysis(
            id=str(uuid4()),
            user_id=self.user.id,
            analysis_type=analysis_type,
            image_reference=image_reference,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def record(self, payload: AiCorrectionCreate) -> list[AiCorrectionPublic]:
        analysis = None
        if payload.analysis_id:
            analysis = self.db.execute(
                select(AiAnalysis).where(
                    AiAnalysis.id == payload.analysis_id,
                    AiAnalysis.user_id == self.user.id,
                )
            ).scalar_one_or_none()
        opted_in = bool(self.user.allow_training_data_collection)
        image_reference = analysis.image_reference if analysis else None
        stored: list[AiAnalysisFeedback] = []
        for item in payload.items:
            predicted = item.predicted_name.strip()
            corrected = item.corrected_name.strip()
            confirmed = item.confirmed
            if confirmed is None:
                confirmed = (
                    predicted.lower() == corrected.lower()
                    and item.predicted_quantity == item.corrected_quantity
                    and item.predicted_unit.strip().lower() == item.corrected_unit.strip().lower()
                )
            row = AiAnalysisFeedback(
                user_id=self.user.id,
                analysis_id=analysis.id if analysis else None,
                image_reference=image_reference,
                predicted_food=predicted,
                corrected_food=corrected,
                predicted_quantity=Decimal(item.predicted_quantity),
                corrected_quantity=Decimal(item.corrected_quantity),
                predicted_unit=item.predicted_unit.strip(),
                corrected_unit=item.corrected_unit.strip(),
                predicted_confidence=Decimal(str(item.predicted_confidence)) if item.predicted_confidence is not None else None,
                confirmed=bool(confirmed),
                include_in_training=bool(opted_in and image_reference),
            )
            self.db.add(row)
            stored.append(row)
        self.db.commit()
        for row in stored:
            self.db.refresh(row)
        return [
            AiCorrectionPublic(
                id=row.id,
                food=row.corrected_food,
                predicted_quantity=row.predicted_quantity,
                predicted_unit=row.predicted_unit,
                corrected_quantity=row.corrected_quantity,
                corrected_unit=row.corrected_unit,
                predicted_name=row.predicted_food,
                corrected_name=row.corrected_food,
                confirmed=row.confirmed,
                include_in_training=row.include_in_training,
                analysis_id=row.analysis_id,
            )
            for row in stored
        ]
