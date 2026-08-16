from pathlib import Path

from training.config import QualityGateConfig
from training.dataset import class_balance_report, split_by_session
from training.metrics import classification_metrics
from training.pipeline import run_pipeline
from training.quality import ModelScores, apply_quality_gate
from training.records import Sample, sample_to_dict, write_jsonl
from training.registry import ensure_baseline, load_registry, next_version, production_model, promote, register_candidate, rollback
from training.train import InsufficientTrainingData, MajorityClassTrainer
from training.validate import find_duplicates, validate_dataset

MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c089"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _sample(**kwargs) -> Sample:
    base = dict(
        image_path="raw/images/a.png",
        food_label="rice",
        quantity=1.0,
        unit="cup",
        source="user_feedback",
        created_at="2026-08-16T00:00:00+00:00",
        analysis_id="session-a",
        confirmed=False,
        predicted_food="rice",
        predicted_quantity=1.0,
        predicted_unit="cup",
        corrected_quantity=1.0,
        corrected_unit="cup",
        sample_id="s1",
    )
    base.update(kwargs)
    return Sample(**base)


def _write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(MIN_PNG)


def test_validate_rejects_bad_and_duplicate_samples(tmp_path: Path) -> None:
    data = tmp_path / "data"
    good = data / "raw" / "images" / "a.png"
    _write_png(good)
    samples = [
        _sample(image_path="raw/images/a.png", sample_id="ok"),
        _sample(image_path="raw/images/missing.png", sample_id="missing", analysis_id="b"),
        _sample(image_path="raw/images/a.png", quantity=0, sample_id="qty", analysis_id="c"),
        _sample(image_path="raw/images/a.png", unit="furlong", sample_id="unit", analysis_id="d"),
        _sample(image_path="raw/images/a.png", food_label="", sample_id="label", analysis_id="e"),
        _sample(image_path="raw/images/a.png", sample_id="dup"),
    ]
    report = validate_dataset(samples, data_root=data)
    assert report["accepted_count"] == 1
    reasons = {item["sample_id"]: item["reasons"] for item in report["rejected"]}
    assert "image_missing" in reasons["missing"]
    assert "non_positive_quantity" in reasons["qty"]
    assert "invalid_unit" in reasons["unit"]
    assert "missing_food_label" in reasons["label"]
    assert "duplicate_sample" in reasons["dup"]
    assert find_duplicates(samples[:1] + samples[:1], data_root=data)


def test_split_keeps_session_together() -> None:
    samples = []
    for session in range(10):
        for index in range(2):
            samples.append(
                _sample(
                    analysis_id=f"s{session}",
                    sample_id=f"s{session}-{index}",
                    food_label="rice" if session < 7 else "dal",
                )
            )
    splits = split_by_session(samples, seed=42)
    membership = {}
    for name, group in splits.items():
        for item in group:
            membership.setdefault(item.analysis_id, set()).add(name)
    assert all(len(splits_for_session) == 1 for splits_for_session in membership.values())
    assert splits["test"]
    assert sum(len(group) for group in splits.values()) == 20


def test_class_balance_reports_underrepresented() -> None:
    samples = [_sample(food_label="rice", analysis_id=f"r{i}", sample_id=f"r{i}") for i in range(20)]
    samples += [_sample(food_label="dal", analysis_id=f"d{i}", sample_id=f"d{i}") for i in range(15)]
    samples += [_sample(food_label="chapati", analysis_id="c1", sample_id="c1")]
    report = class_balance_report({"train": samples, "validation": [], "test": []})
    assert report["samples_per_food"]["chapati"] == 1
    assert "chapati" in report["underrepresented_classes"]
    assert "oversampling" not in report["balancing_strategy"].lower() or "No automatic oversampling" in report["balancing_strategy"]


def test_quality_gate_requires_improvement() -> None:
    config = QualityGateConfig()
    win = apply_quality_gate(
        current=ModelScores(accuracy=0.912, f1=0.91),
        candidate=ModelScores(accuracy=0.941, f1=0.94),
        config=config,
    )
    assert win["quality_gate"] == "PASSED"
    assert win["recommendation"] == "APPROVAL_REQUIRED"
    lose = apply_quality_gate(
        current=ModelScores(accuracy=0.912, f1=0.91),
        candidate=ModelScores(accuracy=0.897, f1=0.89),
        config=config,
    )
    assert lose["quality_gate"] == "FAILED"
    assert lose["recommendation"] == "REJECT"


def test_registry_promote_and_rollback(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    ensure_baseline(path)
    v1 = next_version(load_registry(path))
    register_candidate(path, version=v1, training_dataset_version="d1", metrics={"accuracy": 0.94, "precision": 0.94, "recall": 0.94, "f1": 0.94})
    promote(path, v1)
    assert production_model(load_registry(path))["version"] == v1
    v2 = next_version(load_registry(path))
    register_candidate(path, version=v2, training_dataset_version="d2", metrics={"accuracy": 0.80, "precision": 0.8, "recall": 0.8, "f1": 0.8})
    promote(path, v2)
    assert production_model(load_registry(path))["version"] == v2
    rollback(path, v1)
    registry = load_registry(path)
    assert production_model(registry)["version"] == v1
    assert sum(1 for item in registry["models"] if item["status"] == "production") == 1


def test_majority_trainer_refuses_small_sets(tmp_path: Path) -> None:
    data = tmp_path / "data"
    for split in ("train", "validation", "test"):
        write_jsonl(data / split / "samples.jsonl", [])
    trainer = MajorityClassTrainer(data, min_samples=50)
    trainer.prepare_dataset()
    try:
        trainer.train()
        raise AssertionError("expected skip")
    except InsufficientTrainingData:
        pass


def test_pipeline_does_not_deploy(tmp_path: Path) -> None:
    data = tmp_path / "data"
    rows = []
    for index in range(6):
        name = f"{index}.png"
        image = data / "raw" / "images" / name
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(MIN_PNG + bytes([index]))
        sample = _sample(
            image_path=f"raw/images/{name}",
            analysis_id=f"s{index}",
            sample_id=str(index),
            food_label="rice" if index < 4 else "dal",
            confirmed=False,
        )
        rows.append(sample_to_dict(sample))
    write_jsonl(data / "raw" / "feedback.jsonl", rows)
    (tmp_path / "quality_gate.json").write_text(
        '{"minimum_accuracy": 0.0, "minimum_f1": 0.0, "minimum_improvement": 0.0, "auto_promote": false, "min_samples_to_train": 4, "include_confirmed_in_training": false}',
        encoding="utf-8",
    )
    report = run_pipeline(tmp_path, min_samples_override=4)
    assert report["deployed"] is False
    assert report["recommendation"] in {"APPROVAL_REQUIRED", "REJECT", "AUTO_PROMOTE_CONFIGURED", "DO_NOT_TRAIN"}
    assert (tmp_path / "reports" / "latest.json").exists()
    statuses = [item["status"] for item in load_registry(tmp_path / "models" / "registry.json")["models"]]
    assert statuses.count("production") == 1


def test_classification_metrics_confusion() -> None:
    metrics = classification_metrics(
        ["rice", "rice", "dosa", "chapati"],
        ["rice", "biryani", "idli", "roti"],
    )
    assert metrics["confusion_matrix"]["rice"]["rice"] == 1
    assert metrics["confusion_matrix"]["rice"]["biryani"] == 1
    assert metrics["accuracy"] == 0.25
