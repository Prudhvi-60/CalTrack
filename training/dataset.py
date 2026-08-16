from __future__ import annotations

import random
from collections import Counter
from pathlib import Path
import shutil

from training.config import (
    RANDOM_SEED,
    TEST_RATIO,
    TRAIN_RATIO,
    VALIDATION_RATIO,
    load_quality_gate,
)
from training.records import Sample, sample_to_dict, write_jsonl


def split_by_session(
    samples: list[Sample],
    *,
    seed: int = RANDOM_SEED,
    train_ratio: float = TRAIN_RATIO,
    validation_ratio: float = VALIDATION_RATIO,
    test_ratio: float = TEST_RATIO,
) -> dict[str, list[Sample]]:
    if abs(train_ratio + validation_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("split ratios must sum to 1")
    groups: dict[str, list[Sample]] = {}
    for sample in samples:
        groups.setdefault(sample.analysis_id, []).append(sample)
    keys = sorted(groups)
    rng = random.Random(seed)
    rng.shuffle(keys)
    total = len(keys)
    n_train = int(total * train_ratio)
    n_val = int(total * validation_ratio)
    if total >= 3 and n_train + n_val >= total:
        n_val = max(1, total - n_train - 1)
        n_train = total - n_val - 1
    elif total == 2:
        n_train, n_val = 1, 0
    elif total == 1:
        n_train, n_val = 1, 0
    train_keys = set(keys[:n_train])
    val_keys = set(keys[n_train : n_train + n_val])
    test_keys = set(keys[n_train + n_val :])
    splits = {"train": [], "validation": [], "test": []}
    for key, group in groups.items():
        if key in train_keys:
            target = "train"
        elif key in val_keys:
            target = "validation"
        else:
            target = "test"
        for sample in group:
            sample.split = target
            splits[target].append(sample)
    return splits


def class_balance_report(splits: dict[str, list[Sample]], *, underrepresented_ratio: float = 0.25) -> dict:
    all_samples = [item for group in splits.values() for item in group]
    per_food = Counter(item.food_label.lower() for item in all_samples)
    if not per_food:
        mean = 0.0
        underrepresented = []
    else:
        mean = sum(per_food.values()) / len(per_food)
        underrepresented = sorted(
            food for food, count in per_food.items() if count < mean * underrepresented_ratio or count < 5
        )
    return {
        "samples_per_food": dict(sorted(per_food.items())),
        "samples_per_class": dict(sorted(per_food.items())),
        "training_samples": len(splits.get("train", [])),
        "validation_samples": len(splits.get("validation", [])),
        "test_samples": len(splits.get("test", [])),
        "underrepresented_classes": underrepresented,
        "balancing_strategy": (
            "No automatic oversampling. Underrepresented classes are reported only. "
            "Collect more opted-in corrected examples before training."
        ),
        "mean_per_class": mean,
    }


def copy_split_images(splits: dict[str, list[Sample]], *, data_root: Path, destinations: dict[str, Path]) -> None:
    for split, samples in splits.items():
        dest = destinations[split]
        dest.mkdir(parents=True, exist_ok=True)
        for child in dest.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_file():
                child.unlink()
        for sample in samples:
            source = data_root / sample.image_path if not Path(sample.image_path).is_absolute() else Path(sample.image_path)
            if source.exists():
                target = dest / f"{sample.sample_id.replace(':', '_')}{source.suffix}"
                shutil.copy2(source, target)


def build_dataset(
    samples: list[Sample],
    *,
    data_root: Path,
    destinations: dict[str, Path],
    dataset_jsonl: Path,
    seed: int = RANDOM_SEED,
    include_confirmed: bool | None = None,
) -> dict:
    gate = load_quality_gate(data_root.parent if data_root.name == "data" else None)
    use_confirmed = gate.include_confirmed_in_training if include_confirmed is None else include_confirmed
    eligible = [item for item in samples if use_confirmed or not item.confirmed]
    splits = split_by_session(eligible, seed=seed)
    copy_split_images(splits, data_root=data_root, destinations=destinations)
    all_rows = []
    for split, group in splits.items():
        write_jsonl(destinations[split] / "samples.jsonl", [sample_to_dict(item) for item in group])
        all_rows.extend(sample_to_dict(item) for item in group)
    write_jsonl(dataset_jsonl, all_rows)
    balance = class_balance_report(splits)
    return {
        "splits": {name: len(group) for name, group in splits.items()},
        "balance": balance,
        "included_confirmed": use_confirmed,
        "eligible_count": len(eligible),
        "held_out_confirmed": len(samples) - len(eligible),
        "seed": seed,
        "leakage_guard": "split_by_analysis_id",
    }
