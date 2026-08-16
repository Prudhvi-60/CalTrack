from __future__ import annotations

import argparse
from pathlib import Path

from training.collect import collect_feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="Export opted-in feedback into training/data/raw/collected.jsonl")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    samples = collect_feedback(args.root)
    print(f"collected {len(samples)} opted-in samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
