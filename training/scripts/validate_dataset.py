from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.collect import collect_feedback
from training.config import default_paths
from training.validate import validate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CalTrack training samples.")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    paths = default_paths(args.root)
    samples = collect_feedback(args.root)
    report = validate_dataset(samples, data_root=paths["data"])
    public = {key: value for key, value in report.items() if key != "accepted"}
    paths["reports"].mkdir(parents=True, exist_ok=True)
    paths["validation_report"].write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: public[k] for k in ("input_count", "accepted_count", "rejected_count")}, indent=2))
    return 0 if report["rejected_count"] == 0 or report["accepted_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
