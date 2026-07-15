"""GPU workload reduction metrics."""

from __future__ import annotations


def reduction_ratio(baseline: float, candidate: float) -> float:
    if baseline <= 0:
        return 0.0
    return max(0.0, (baseline - candidate) / baseline)
