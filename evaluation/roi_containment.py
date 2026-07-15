"""ROI containment metrics."""

from __future__ import annotations

from common import ROI


def contains_bbox(roi: ROI, bbox_xyxy: list[float]) -> bool:
    x1, y1, x2, y2 = bbox_xyxy
    return roi.x <= x1 and roi.y <= y1 and roi.x + roi.w >= x2 and roi.y + roi.h >= y2
