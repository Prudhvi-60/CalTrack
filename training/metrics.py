from __future__ import annotations

from math import isfinite


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return num / den


def classification_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred length mismatch")
    labels = sorted(set(y_true) | set(y_pred))
    matrix: dict[str, dict[str, int]] = {actual: {pred: 0 for pred in labels} for actual in labels}
    for actual, pred in zip(y_true, y_pred, strict=True):
        matrix[actual][pred] += 1
    correct = sum(1 for actual, pred in zip(y_true, y_pred, strict=True) if actual == pred)
    accuracy = _safe_div(correct, len(y_true)) if y_true else 0.0
    per_class: dict[str, dict[str, float]] = {}
    precisions = []
    recalls = []
    f1s = []
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall) if precision + recall else 0.0
        support = sum(matrix[label].values())
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": _safe_div(tp, support) if support else 0.0,
            "support": support,
        }
        if support:
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
    return {
        "accuracy": accuracy,
        "precision": sum(precisions) / len(precisions) if precisions else 0.0,
        "recall": sum(recalls) / len(recalls) if recalls else 0.0,
        "f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "per_class": per_class,
        "confusion_matrix": matrix,
        "n": len(y_true),
        "notes": "Precision, recall, and F1 are macro-averaged over classes present in y_true.",
    }


def quantity_metrics(y_true: list[float], y_pred: list[float]) -> dict:
    if len(y_true) != len(y_pred):
        raise ValueError("quantity length mismatch")
    if not y_true:
        return {"mae": None, "mape": None, "n": 0, "notes": "No quantity pairs to score."}
    errors = [abs(actual - pred) for actual, pred in zip(y_true, y_pred, strict=True)]
    mae = sum(errors) / len(errors)
    mape_terms = []
    skipped = 0
    for actual, pred in zip(y_true, y_pred, strict=True):
        if actual == 0 or not isfinite(actual):
            skipped += 1
            continue
        mape_terms.append(abs(actual - pred) / abs(actual))
    mape = (sum(mape_terms) / len(mape_terms)) if mape_terms else None
    return {
        "mae": mae,
        "mape": mape,
        "n": len(y_true),
        "mape_skipped_zero_actual": skipped,
        "notes": "MAPE omitted for zero actual quantities. Quantity is a separate task from food classification.",
    }


def flatten_confusion(matrix: dict[str, dict[str, int]]) -> list[dict]:
    rows = []
    for actual, preds in matrix.items():
        for pred, count in preds.items():
            if count:
                rows.append({"actual": actual, "predicted": pred, "count": count})
    return rows
