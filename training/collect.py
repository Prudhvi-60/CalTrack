from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from training.config import default_paths, normalize_unit
from training.records import Sample, now_iso, read_jsonl, sample_from_dict, sample_to_dict, write_jsonl


def feedback_row_to_sample(row: dict, *, data_root: Path) -> Sample | None:
    if not row.get("include_in_training"):
        return None
    image_reference = row.get("image_reference")
    if not image_reference:
        return None
    image_path = f"raw/images/{image_reference}"
    if not (data_root / image_path).exists():
        return None
    food = str(row.get("corrected_food") or "").strip()
    unit = normalize_unit(str(row.get("corrected_unit") or ""))
    analysis_id = str(row.get("analysis_id") or uuid4())
    return Sample(
        image_path=image_path,
        food_label=food,
        quantity=float(row.get("corrected_quantity") or 0),
        unit=unit,
        source="user_feedback",
        created_at=str(row.get("created_at") or now_iso()),
        analysis_id=analysis_id,
        confirmed=bool(row.get("confirmed")),
        predicted_food=str(row.get("predicted_food") or food),
        predicted_quantity=float(row.get("predicted_quantity") or 0),
        predicted_unit=normalize_unit(str(row.get("predicted_unit") or unit)),
        corrected_quantity=float(row.get("corrected_quantity") or 0),
        corrected_unit=unit,
        sample_id=str(row.get("id") or f"{analysis_id}:{food}"),
    )


def collect_from_jsonl(path: Path, *, data_root: Path) -> list[Sample]:
    samples: list[Sample] = []
    for row in read_jsonl(path):
        if "food_label" in row and "image_path" in row:
            samples.append(sample_from_dict(row))
            continue
        sample = feedback_row_to_sample(row, data_root=data_root)
        if sample is not None:
            samples.append(sample)
    return samples


def collect_from_database(*, data_root: Path) -> list[Sample]:
    """Optional live export. Skipped if the backend app is not importable."""
    try:
        import sys

        backend = Path(__file__).resolve().parents[1] / "backend"
        if str(backend) not in sys.path:
            sys.path.insert(0, str(backend))
        from sqlalchemy import select
        from app.db.session import SessionLocal
        from app.models import AiAnalysisFeedback
    except Exception:
        return []

    samples: list[Sample] = []
    db = SessionLocal()
    try:
        rows = db.execute(select(AiAnalysisFeedback).where(AiAnalysisFeedback.include_in_training.is_(True))).scalars()
        for row in rows:
            payload = {
                "id": row.id,
                "include_in_training": row.include_in_training,
                "image_reference": row.image_reference,
                "corrected_food": row.corrected_food,
                "corrected_quantity": row.corrected_quantity,
                "corrected_unit": row.corrected_unit,
                "predicted_food": row.predicted_food,
                "predicted_quantity": row.predicted_quantity,
                "predicted_unit": row.predicted_unit,
                "confirmed": row.confirmed,
                "analysis_id": row.analysis_id,
                "created_at": row.created_at.isoformat() if row.created_at else now_iso(),
            }
            sample = feedback_row_to_sample(payload, data_root=data_root)
            if sample is not None:
                samples.append(sample)
    finally:
        db.close()
    return samples


def collect_feedback(root: Path | None = None) -> list[Sample]:
    paths = default_paths(root)
    data_root = paths["data"]
    samples = collect_from_jsonl(paths["raw_feedback"], data_root=data_root)
    if not samples:
        samples = collect_from_database(data_root=data_root)
    write_jsonl(data_root / "raw" / "collected.jsonl", [sample_to_dict(sample) for sample in samples])
    return samples
