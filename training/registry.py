from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from training.config import MODEL_NAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"models": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def production_model(registry: dict[str, Any]) -> dict[str, Any] | None:
    matches = [item for item in registry.get("models", []) if item.get("status") == "production"]
    if len(matches) > 1:
        raise ValueError("multiple production models in registry")
    return matches[0] if matches else None


def next_version(registry: dict[str, Any], model_name: str = MODEL_NAME) -> str:
    highest = 0
    prefix = f"{model_name}-v"
    for item in registry.get("models", []):
        version = str(item.get("version", ""))
        if version.startswith(prefix):
            suffix = version[len(prefix) :]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1}"


def register_candidate(
    path: Path,
    *,
    version: str,
    training_dataset_version: str,
    metrics: dict[str, float | None],
    model_name: str = MODEL_NAME,
    checkpoint: str | None = None,
) -> dict[str, Any]:
    registry = load_registry(path)
    if any(item.get("version") == version for item in registry.get("models", [])):
        raise ValueError(f"version already exists: {version}")
    entry = {
        "model_name": model_name,
        "version": version,
        "training_dataset_version": training_dataset_version,
        "accuracy": metrics.get("accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
        "created_at": _now(),
        "status": "candidate",
        "checkpoint": checkpoint,
    }
    registry.setdefault("models", []).append(entry)
    save_registry(path, registry)
    return entry


def _find(registry: dict[str, Any], version: str) -> dict[str, Any]:
    for item in registry.get("models", []):
        if item.get("version") == version:
            return item
    raise KeyError(version)


def promote(path: Path, version: str) -> dict[str, Any]:
    registry = load_registry(path)
    target = _find(registry, version)
    if target["status"] not in {"candidate", "approved"}:
        raise ValueError("only candidate or approved models can be promoted")
    for item in registry["models"]:
        if item["status"] == "production":
            item["status"] = "approved"
            item["demoted_at"] = _now()
    target["status"] = "production"
    target["promoted_at"] = _now()
    save_registry(path, registry)
    return target


def reject(path: Path, version: str) -> dict[str, Any]:
    registry = load_registry(path)
    target = _find(registry, version)
    if target["status"] == "production":
        raise ValueError("reject production via rollback instead")
    target["status"] = "rejected"
    target["rejected_at"] = _now()
    save_registry(path, registry)
    return target


def rollback(path: Path, version: str) -> dict[str, Any]:
    registry = load_registry(path)
    target = _find(registry, version)
    current = production_model(registry)
    if current is not None and current["version"] == version:
        return current
    if current is not None:
        current["status"] = "rejected"
        current["rolled_back_at"] = _now()
    target["status"] = "production"
    target["restored_at"] = _now()
    save_registry(path, registry)
    return target


def ensure_baseline(path: Path) -> dict[str, Any]:
    registry = load_registry(path)
    if production_model(registry):
        return production_model(registry)  # type: ignore[return-value]
    entry = {
        "model_name": MODEL_NAME,
        "version": f"{MODEL_NAME}-v0",
        "training_dataset_version": "none",
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "created_at": _now(),
        "status": "production",
        "notes": "External cloud vision. Nutrition from the CalTrack database. Not a local classifier.",
    }
    registry.setdefault("models", []).append(entry)
    save_registry(path, registry)
    return entry
