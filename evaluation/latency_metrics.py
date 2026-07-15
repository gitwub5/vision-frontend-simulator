"""Latency metric helpers."""

from __future__ import annotations


def average_ms(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
