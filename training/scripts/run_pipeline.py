from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run collect → validate → split → train → evaluate → quality gate.")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    report = run_pipeline(args.root)
    print(json.dumps({
        "candidate_accuracy": report.get("candidate_accuracy"),
        "current_accuracy": report.get("current_accuracy"),
        "improvement": report.get("improvement"),
        "quality_gate": report.get("quality_gate"),
        "recommendation": report.get("recommendation"),
        "deployed": report.get("deployed"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
