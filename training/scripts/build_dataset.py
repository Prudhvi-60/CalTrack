from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.collect import collect_feedback
from training.config import default_paths
from training.dataset import build_dataset
from training.validate import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Build train/validation/test splits without leakage.")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    paths = default_paths(args.root)
    samples = collect_feedback(args.root)
    report = validate_dataset(samples, data_root=paths["data"])
    built = build_dataset(
        report["accepted"],
        data_root=paths["data"],
        destinations={"train": paths["train"], "validation": paths["validation"], "test": paths["test"]},
        dataset_jsonl=paths["dataset_jsonl"],
    )
    paths["class_balance"].write_text(json.dumps(built["balance"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"splits": built["splits"], "underrepresented": built["balance"]["underrepresented_classes"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
