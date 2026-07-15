"""Detection-level comparison metrics."""

from __future__ import annotations


def recall_retention(full_frame_recall: float, roi_gated_recall: float) -> float:
    if full_frame_recall == 0:
        return 0.0
    return roi_gated_recall / full_frame_recall
