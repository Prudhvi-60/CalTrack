from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import Counter
from pathlib import Path

from training.config import load_quality_gate
from training.metrics import classification_metrics, quantity_metrics
from training.records import read_jsonl, sample_from_dict


class InsufficientTrainingData(RuntimeError):
    pass


class ModelTrainer(ABC):
    @abstractmethod
    def prepare_dataset(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def train(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, split: str = "validation") -> dict:
        raise NotImplementedError

    @abstractmethod
    def save_checkpoint(self, path: Path) -> Path:
        raise NotImplementedError


class MajorityClassTrainer(ModelTrainer):
    """Placeholder trainer: predicts the majority training food label.

    This is not a production vision model. It exists so the pipeline, metrics,
    registry, and quality gate can be tested without training a multimodal network.
    """

    def __init__(self, data_root: Path, min_samples: int | None = None) -> None:
        self.data_root = data_root
        self.min_samples = min_samples if min_samples is not None else load_quality_gate(data_root.parent).min_samples_to_train
        self.label: str | None = None
        self.mean_quantity: float | None = None
        self.prepared: dict[str, list] = {}

    def prepare_dataset(self) -> dict:
        prepared = {}
        for split in ("train", "validation", "test"):
            rows = read_jsonl(self.data_root / split / "samples.jsonl")
            prepared[split] = [sample_from_dict(row) for row in rows]
        self.prepared = prepared
        return {name: len(items) for name, items in prepared.items()}

    def train(self) -> dict:
        if not self.prepared:
            self.prepare_dataset()
        train = self.prepared["train"]
        if len(train) < self.min_samples:
            raise InsufficientTrainingData(
                f"Need at least {self.min_samples} validated training samples; found {len(train)}. "
                "Do not train until more opted-in corrections exist."
            )
        labels = [item.food_label.lower() for item in train]
        self.label = Counter(labels).most_common(1)[0][0]
        quantities = [item.quantity for item in train]
        self.mean_quantity = sum(quantities) / len(quantities)
        return {
            "trainer": "majority_class",
            "label": self.label,
            "train_samples": len(train),
            "warning": "Majority-class baseline only. Not a fine-tuned vision model.",
        }

    def evaluate(self, split: str = "validation") -> dict:
        if self.label is None:
            raise RuntimeError("train() must be called first")
        rows = self.prepared.get(split) or []
        y_true = [item.food_label.lower() for item in rows]
        y_pred = [self.label for _ in rows]
        cls = classification_metrics(y_true, y_pred)
        qty = quantity_metrics([item.quantity for item in rows], [self.mean_quantity or 0 for _ in rows])
        return {"split": split, "classification": cls, "quantity": qty}

    def save_checkpoint(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "trainer": "majority_class",
            "label": self.label,
            "mean_quantity": self.mean_quantity,
            "not_a_vision_model": True,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path
