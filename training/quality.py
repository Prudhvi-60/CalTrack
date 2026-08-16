from __future__ import annotations

from dataclasses import dataclass

from training.config import QualityGateConfig


@dataclass
class ModelScores:
    accuracy: float | None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None


def apply_quality_gate(
    *,
    current: ModelScores,
    candidate: ModelScores,
    config: QualityGateConfig,
) -> dict:
    reasons: list[str] = []
    if candidate.accuracy is None or candidate.f1 is None:
        return {
            "quality_gate": "FAILED",
            "recommendation": "REJECT",
            "improvement": None,
            "reasons": ["candidate_metrics_missing"],
            "auto_promote": config.auto_promote,
            "thresholds": {
                "minimum_accuracy": config.minimum_accuracy,
                "minimum_f1": config.minimum_f1,
                "minimum_improvement": config.minimum_improvement,
            },
            "candidate_accuracy": candidate.accuracy,
            "current_accuracy": current.accuracy,
            "candidate_f1": candidate.f1,
            "current_f1": current.f1,
        }

    if candidate.accuracy < config.minimum_accuracy:
        reasons.append("accuracy_below_minimum")
    if candidate.f1 < config.minimum_f1:
        reasons.append("f1_below_minimum")

    improvement = None
    if current.accuracy is not None:
        improvement = candidate.accuracy - current.accuracy
        if candidate.accuracy < current.accuracy:
            reasons.append("worse_than_current")
        elif improvement < config.minimum_improvement:
            reasons.append("insufficient_improvement")
    else:
        reasons.append("no_current_local_baseline")

    hard_fail = {
        "accuracy_below_minimum",
        "f1_below_minimum",
        "worse_than_current",
        "insufficient_improvement",
    }
    passed = not any(reason in hard_fail for reason in reasons)
    if passed and not config.auto_promote:
        recommendation = "APPROVAL_REQUIRED"
    elif passed:
        recommendation = "AUTO_PROMOTE_CONFIGURED"
    else:
        recommendation = "REJECT"
    return {
        "quality_gate": "PASSED" if passed else "FAILED",
        "recommendation": recommendation,
        "improvement": improvement,
        "reasons": reasons,
        "auto_promote": config.auto_promote,
        "thresholds": {
            "minimum_accuracy": config.minimum_accuracy,
            "minimum_f1": config.minimum_f1,
            "minimum_improvement": config.minimum_improvement,
        },
        "candidate_accuracy": candidate.accuracy,
        "current_accuracy": current.accuracy,
        "candidate_f1": candidate.f1,
        "current_f1": current.f1,
    }
