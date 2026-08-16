from __future__ import annotations

import argparse
import json
from pathlib import Path

from training.config import default_paths
from training.registry import promote, reject, rollback


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote, reject, or roll back a registered model. Never trains.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--promote")
    parser.add_argument("--reject")
    parser.add_argument("--rollback")
    args = parser.parse_args()
    registry = default_paths(args.root)["registry"]
    if args.promote:
        print(json.dumps(promote(registry, args.promote), indent=2))
        return 0
    if args.reject:
        print(json.dumps(reject(registry, args.reject), indent=2))
        return 0
    if args.rollback:
        print(json.dumps(rollback(registry, args.rollback), indent=2))
        return 0
    parser.error("specify --promote, --reject, or --rollback")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
