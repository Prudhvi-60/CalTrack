from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from training import ROOT

VALID_UNITS = frozenset(
    {
        "cup",
        "bowl",
        "plate",
        "tbsp",
        "tsp",
        "g",
        "kg",
        "ml",
        "piece",
        "serving",
    }
)

UNIT_ALIASES = {
    "cups": "cup",
    "cup": "cup",
    "c": "cup",
    "bowl": "bowl",
    "bowls": "bowl",
    "plate": "plate",
    "plates": "plate",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",
    "tbs": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "gram": "g",
    "grams": "g",
    "gm": "g",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
    "l": "ml",
    "liter": "ml",
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "count": "piece",
    "item": "piece",
    "items": "piece",
    "serving": "serving",
    "servings": "serving",
}

RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15
MAX_QUANTITY = 30.0
MIN_SAMPLES_TO_TRAIN = 50
UNDERREPRESENTED_RATIO = 0.25
MODEL_NAME = "caltrack-food"


@dataclass(frozen=True)
class QualityGateConfig:
    minimum_accuracy: float = 0.90
    minimum_f1: float = 0.90
    minimum_improvement: float = 0.01
    auto_promote: bool = False
    min_samples_to_train: int = MIN_SAMPLES_TO_TRAIN
    include_confirmed_in_training: bool = False


def default_paths(root: Path | None = None) -> dict[str, Path]:
    base = root or ROOT
    data = base / "data"
    return {
        "root": base,
        "data": data,
        "raw": data / "raw",
        "raw_images": data / "raw" / "images",
        "raw_feedback": data / "raw" / "feedback.jsonl",
        "train": data / "train",
        "validation": data / "validation",
        "test": data / "test",
        "dataset_jsonl": data / "dataset.jsonl",
        "models": base / "models",
        "checkpoints": base / "models" / "checkpoints",
        "registry": base / "models" / "registry.json",
        "reports": base / "reports",
        "latest_report": base / "reports" / "latest.json",
        "quality_gate": base / "quality_gate.json",
        "confusion_matrix": base / "reports" / "confusion_matrix.json",
        "class_balance": base / "reports" / "class_balance.json",
        "validation_report": base / "reports" / "validation.json",
    }


def load_quality_gate(root: Path | None = None) -> QualityGateConfig:
    path = default_paths(root)["quality_gate"]
    if not path.exists():
        return QualityGateConfig()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return QualityGateConfig(
        minimum_accuracy=float(payload.get("minimum_accuracy", 0.90)),
        minimum_f1=float(payload.get("minimum_f1", 0.90)),
        minimum_improvement=float(payload.get("minimum_improvement", 0.01)),
        auto_promote=bool(payload.get("auto_promote", False)),
        min_samples_to_train=int(payload.get("min_samples_to_train", MIN_SAMPLES_TO_TRAIN)),
        include_confirmed_in_training=bool(payload.get("include_confirmed_in_training", False)),
    )


def normalize_unit(unit: str) -> str:
    return UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())
