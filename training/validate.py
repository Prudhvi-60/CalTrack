from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

from training.config import VALID_UNITS, normalize_unit
from training.images import is_readable_image, sniff_image_kind
from training.records import Sample


def validate_sample(sample: Sample, *, data_root: Path) -> list[str]:
    errors: list[str] = []
    image = (data_root / sample.image_path) if not Path(sample.image_path).is_absolute() else Path(sample.image_path)
    if not image.exists():
        errors.append("image_missing")
    else:
        try:
            payload = image.read_bytes()
        except OSError:
            errors.append("image_unreadable")
            payload = b""
        if payload and sniff_image_kind(payload) is None:
            errors.append("invalid_image_format")
        elif payload and not is_readable_image(image):
            errors.append("image_unreadable")
    if not sample.food_label.strip():
        errors.append("missing_food_label")
    if sample.quantity <= 0:
        errors.append("non_positive_quantity")
    unit = normalize_unit(sample.unit)
    if unit not in VALID_UNITS:
        errors.append("invalid_unit")
    if sample.quantity > 30:
        errors.append("impossible_quantity")
    return errors


def duplicate_key(sample: Sample, *, data_root: Path) -> tuple:
    image = (data_root / sample.image_path) if not Path(sample.image_path).is_absolute() else Path(sample.image_path)
    digest = ""
    if image.exists():
        try:
            digest = sha256(image.read_bytes()).hexdigest()
        except OSError:
            digest = sample.image_path
    return (
        digest or sample.image_path,
        sample.food_label.strip().lower(),
        round(sample.quantity, 2),
        normalize_unit(sample.unit),
    )


def find_duplicates(samples: list[Sample], *, data_root: Path) -> set[int]:
    seen: dict[tuple, int] = {}
    rejected: set[int] = set()
    for index, sample in enumerate(samples):
        key = duplicate_key(sample, data_root=data_root)
        if key in seen:
            rejected.add(index)
        else:
            seen[key] = index
    return rejected


def validate_dataset(samples: list[Sample], *, data_root: Path) -> dict:
    accepted: list[Sample] = []
    rejected: list[dict] = []
    duplicate_indexes = find_duplicates(samples, data_root=data_root)
    for index, sample in enumerate(samples):
        reasons = validate_sample(sample, data_root=data_root)
        if index in duplicate_indexes:
            reasons.append("duplicate_sample")
        if reasons:
            rejected.append({"sample_id": sample.sample_id, "reasons": reasons})
        else:
            accepted.append(sample)
    return {
        "input_count": len(samples),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "rejected": rejected,
        "accepted": accepted,
        "class_counts": dict(Counter(item.food_label.lower() for item in accepted)),
    }
