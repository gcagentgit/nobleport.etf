"""
Typology Analytics — Operational Intelligence Metrics

Measures classification quality, operational entropy, coverage gaps,
and lifecycle transitions. This is executive-level intelligence about
the health of the classification system itself.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class EntropySummary:
    """
    Type entropy measures operational chaos.
    Low entropy = predictable business, consistent project types.
    High entropy = unstable intake, inconsistent projects, bad lead quality.
    """
    entropy: float
    max_entropy: float
    normalized: float
    interpretation: str
    dominant_type: str
    dominant_share: float


@dataclass(frozen=True)
class CoverageGap:
    """An expected type that has zero or very low representation."""
    type_name: str
    expected_minimum: int
    actual_count: int
    severity: str


@dataclass(frozen=True)
class TransitionMatrix:
    """Lifecycle stage transition probabilities."""
    from_stage: str
    to_stage: str
    count: int
    probability: float


def compute_entropy(type_counts: dict[str, int]) -> EntropySummary:
    """
    Shannon entropy of operational type distribution.
    Used as a KPI for operational predictability.
    """
    total = sum(type_counts.values())
    if total == 0:
        return EntropySummary(
            entropy=0.0, max_entropy=0.0, normalized=0.0,
            interpretation="No data", dominant_type="none", dominant_share=0.0,
        )

    n_types = len(type_counts)
    max_entropy = math.log2(n_types) if n_types > 1 else 1.0

    entropy = 0.0
    for count in type_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    normalized = entropy / max_entropy if max_entropy > 0 else 0.0

    dominant = max(type_counts, key=type_counts.get)  # type: ignore[arg-type]
    dominant_share = type_counts[dominant] / total

    if normalized < 0.3:
        interpretation = "Low entropy — highly predictable, concentrated business"
    elif normalized < 0.6:
        interpretation = "Moderate entropy — balanced operational mix"
    elif normalized < 0.8:
        interpretation = "High entropy — diverse intake, monitor for instability"
    else:
        interpretation = "Very high entropy — operational chaos, likely bad lead quality"

    return EntropySummary(
        entropy=round(entropy, 3),
        max_entropy=round(max_entropy, 3),
        normalized=round(normalized, 3),
        interpretation=interpretation,
        dominant_type=dominant,
        dominant_share=round(dominant_share, 3),
    )


def detect_coverage_gaps(
    type_counts: dict[str, int],
    expected_types: list[str],
    minimum_threshold: int = 1,
) -> list[CoverageGap]:
    """
    Operational blind spot detection.
    Finds expected types with zero or very low representation.
    """
    gaps: list[CoverageGap] = []
    for expected in expected_types:
        actual = type_counts.get(expected, 0)
        if actual < minimum_threshold:
            severity = "critical" if actual == 0 else "warning"
            gaps.append(CoverageGap(
                type_name=expected,
                expected_minimum=minimum_threshold,
                actual_count=actual,
                severity=severity,
            ))
    return gaps


def compute_transitions(
    events: Sequence[tuple[str, str]],
) -> list[TransitionMatrix]:
    """
    Compute lifecycle transition probabilities from observed (from, to) pairs.
    Used for customer lifecycle intelligence.
    """
    from_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    for from_stage, to_stage in events:
        from_counts[from_stage] += 1
        pair_counts[(from_stage, to_stage)] += 1

    transitions: list[TransitionMatrix] = []
    for (from_s, to_s), count in pair_counts.most_common():
        probability = count / from_counts[from_s] if from_counts[from_s] > 0 else 0.0
        transitions.append(TransitionMatrix(
            from_stage=from_s,
            to_stage=to_s,
            count=count,
            probability=round(probability, 3),
        ))

    return transitions


def classification_accuracy(
    predicted: Sequence[str],
    actual: Sequence[str],
) -> dict[str, float]:
    """
    Simple accuracy and per-class metrics for AI classification governance.
    Used to measure routing mistakes and permit risk prediction failures.
    """
    if len(predicted) != len(actual):
        raise ValueError("predicted and actual must have same length")

    total = len(predicted)
    if total == 0:
        return {"accuracy": 0.0}

    correct = sum(1 for p, a in zip(predicted, actual) if p == a)
    accuracy = correct / total

    classes = set(actual) | set(predicted)
    per_class: dict[str, float] = {}
    for cls in classes:
        tp = sum(1 for p, a in zip(predicted, actual) if p == cls and a == cls)
        fn = sum(1 for p, a in zip(predicted, actual) if p != cls and a == cls)
        precision_denom = sum(1 for p in predicted if p == cls)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / precision_denom if precision_denom > 0 else 0.0
        per_class[cls] = round((2 * precision * recall) / (precision + recall), 3) if (precision + recall) > 0 else 0.0

    return {"accuracy": round(accuracy, 3), **per_class}
