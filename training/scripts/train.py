from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.config import default_paths
from training.train import InsufficientTrainingData, MajorityClassTrainer, ModelTrainer


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a candidate food classifier (skipped if data is insufficient).")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    paths = default_paths(args.root)
    trainer: ModelTrainer = MajorityClassTrainer(paths["data"])
    trainer.prepare_dataset()
    try:
        result = trainer.train()
    except InsufficientTrainingData as exc:
        print(json.dumps({"skipped": True, "reason": str(exc)}, indent=2))
        return 2
    version_dir = paths["checkpoints"] / "latest-unversioned"
    trainer.save_checkpoint(version_dir / "model.json")
    print(json.dumps(result, indent=2))
    print("Checkpoint is unversioned until run_pipeline registers a candidate. Production is unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
