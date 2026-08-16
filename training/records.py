from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Sample:
    image_path: str
    food_label: str
    quantity: float
    unit: str
    source: str
    created_at: str
    analysis_id: str
    confirmed: bool
    predicted_food: str
    predicted_quantity: float
    predicted_unit: str
    corrected_quantity: float
    corrected_unit: str
    sample_id: str
    split: str | None = None

    def metadata(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "food_label": self.food_label,
            "quantity": self.quantity,
            "unit": self.unit,
            "source": self.source,
            "created_at": self.created_at,
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def sample_from_dict(row: dict[str, Any]) -> Sample:
    return Sample(
        image_path=str(row["image_path"]),
        food_label=str(row["food_label"]).strip(),
        quantity=float(row["quantity"]),
        unit=str(row["unit"]),
        source=str(row.get("source", "user_feedback")),
        created_at=str(row.get("created_at") or now_iso()),
        analysis_id=str(row.get("analysis_id") or row.get("sample_id") or row["image_path"]),
        confirmed=bool(row.get("confirmed", False)),
        predicted_food=str(row.get("predicted_food") or row["food_label"]),
        predicted_quantity=float(row.get("predicted_quantity", row["quantity"])),
        predicted_unit=str(row.get("predicted_unit") or row["unit"]),
        corrected_quantity=float(row.get("corrected_quantity", row["quantity"])),
        corrected_unit=str(row.get("corrected_unit") or row["unit"]),
        sample_id=str(row.get("sample_id") or f"{row.get('analysis_id', '')}:{row['food_label']}"),
        split=row.get("split"),
    )


def sample_to_dict(sample: Sample) -> dict[str, Any]:
    return asdict(sample)
