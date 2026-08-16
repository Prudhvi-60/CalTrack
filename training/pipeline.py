from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from training.collect import collect_feedback
from training.config import default_paths, load_quality_gate
from training.dataset import build_dataset
from training.metrics import flatten_confusion
from training.quality import ModelScores, apply_quality_gate
from training.registry import ensure_baseline, next_version, production_model, promote, register_candidate
from training.train import InsufficientTrainingData, MajorityClassTrainer
from training.validate import validate_dataset


def run_pipeline(root: Path | None = None, *, min_samples_override: int | None = None) -> dict:
    paths = default_paths(root)
    for key in ("raw_images", "train", "validation", "test", "reports", "checkpoints"):
        paths[key].mkdir(parents=True, exist_ok=True)
    gate = load_quality_gate(root)
    collected = collect_feedback(root)
    validation = validate_dataset(collected, data_root=paths["data"])
    paths["validation_report"].write_text(json.dumps({k: v for k, v in validation.items() if k != "accepted"}, indent=2) + "\n", encoding="utf-8")
    accepted = validation["accepted"]
    build = build_dataset(
        accepted,
        data_root=paths["data"],
        destinations={"train": paths["train"], "validation": paths["validation"], "test": paths["test"]},
        dataset_jsonl=paths["dataset_jsonl"],
    )
    paths["class_balance"].write_text(json.dumps(build["balance"], indent=2) + "\n", encoding="utf-8")
    ensure_baseline(paths["registry"])
    current = production_model(json.loads(paths["registry"].read_text(encoding="utf-8")))
    trainer = MajorityClassTrainer(paths["data"], min_samples=min_samples_override or gate.min_samples_to_train)
    counts = trainer.prepare_dataset()
    recommendation = "DO_NOT_TRAIN"
    train_result = None
    metrics = None
    gate_result = {
        "quality_gate": "FAILED",
        "recommendation": "DO_NOT_TRAIN",
        "improvement": None,
        "reasons": ["insufficient_validated_data"],
        "candidate_accuracy": None,
        "current_accuracy": current.get("accuracy") if current else None,
    }
    version = None
    report_deployed = False
    try:
        train_result = trainer.train()
        val_metrics = trainer.evaluate("validation")
        test_metrics = trainer.evaluate("test")
        train_metrics = trainer.evaluate("train")
        metrics = {
            "train": train_metrics,
            "validation": val_metrics,
            "test": test_metrics,
        }
        paths["confusion_matrix"].write_text(
            json.dumps(
                {
                    "validation": flatten_confusion(val_metrics["classification"]["confusion_matrix"]),
                    "test": flatten_confusion(test_metrics["classification"]["confusion_matrix"]),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        cls = test_metrics["classification"]
        gate_result = apply_quality_gate(
            current=ModelScores(
                accuracy=current.get("accuracy") if current else None,
                precision=current.get("precision") if current else None,
                recall=current.get("recall") if current else None,
                f1=current.get("f1") if current else None,
            ),
            candidate=ModelScores(
                accuracy=cls["accuracy"],
                precision=cls["precision"],
                recall=cls["recall"],
                f1=cls["f1"],
            ),
            config=gate,
        )
        version = next_version(json.loads(paths["registry"].read_text(encoding="utf-8")))
        checkpoint = trainer.save_checkpoint(paths["checkpoints"] / version / "model.json")
        register_candidate(
            paths["registry"],
            version=version,
            training_dataset_version=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            metrics={
                "accuracy": cls["accuracy"],
                "precision": cls["precision"],
                "recall": cls["recall"],
                "f1": cls["f1"],
            },
            checkpoint=str(checkpoint),
        )
        recommendation = gate_result["recommendation"]
        if gate.auto_promote and gate_result.get("quality_gate") == "PASSED":
            promote(paths["registry"], version)
            report_deployed = True
    except InsufficientTrainingData as exc:
        train_result = {"skipped": True, "reason": str(exc)}
        recommendation = "DO_NOT_TRAIN"

    report = {
        "dataset_size": {
            "collected": len(collected),
            "accepted": len(accepted),
            "rejected": validation["rejected_count"],
            "splits": counts,
        },
        "class_distribution": build["balance"],
        "training_metrics": None if not metrics else metrics["train"]["classification"],
        "validation_metrics": None if not metrics else metrics["validation"]["classification"],
        "test_metrics": None if not metrics else metrics["test"]["classification"],
        "quantity_metrics": None if not metrics else metrics["test"]["quantity"],
        "current_model_metrics": current,
        "candidate_metrics": None if not metrics else metrics["test"]["classification"],
        "candidate_accuracy": gate_result.get("candidate_accuracy"),
        "current_accuracy": gate_result.get("current_accuracy"),
        "improvement": gate_result.get("improvement"),
        "quality_gate": gate_result.get("quality_gate"),
        "recommendation": recommendation,
        "quality_gate_detail": gate_result,
        "train_result": train_result,
        "candidate_version": version,
        "deployed": report_deployed,
        "notes": [
            "Test split is isolated and was not used for training.",
            "Production is never replaced automatically unless auto_promote is enabled.",
            "Food classification is the training target; calories still come from the nutrition database.",
        ],
    }
    paths["latest_report"].write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return report
