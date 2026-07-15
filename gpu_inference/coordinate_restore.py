"""Coordinate conversion from ROI crop space to original frame space."""

from __future__ import annotations

from common import ROI


def restore_xyxy_from_crop(bbox_xyxy: list[float], roi: ROI) -> list[float]:
    x1, y1, x2, y2 = bbox_xyxy
    return [x1 + roi.x, y1 + roi.y, x2 + roi.x, y2 + roi.y]
