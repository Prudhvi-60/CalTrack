from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.config import default_paths
from training.metrics import flatten_confusion
from training.train import InsufficientTrainingData, MajorityClassTrainer


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a trained candidate on the isolated test split.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--split", default="test")
    args = parser.parse_args()
    paths = default_paths(args.root)
    trainer = MajorityClassTrainer(paths["data"])
    trainer.prepare_dataset()
    try:
        trainer.train()
    except InsufficientTrainingData as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, indent=2))
        return 2
    metrics = trainer.evaluate(args.split)
    paths["reports"].mkdir(parents=True, exist_ok=True)
    paths["confusion_matrix"].write_text(
        json.dumps(flatten_confusion(metrics["classification"]["confusion_matrix"]), indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "accuracy": metrics["classification"]["accuracy"],
        "precision": metrics["classification"]["precision"],
        "recall": metrics["classification"]["recall"],
        "f1": metrics["classification"]["f1"],
        "quantity": metrics["quantity"],
        "split": args.split,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
