"""Dataclasses shared across loader, gate, inference, and evaluation code."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TriggerType(StrEnum):
    ROI = "roi"
    HOLD = "temporal_hold"
    FULL_FRAME = "full_frame"
    FALLBACK_FULL_FRAME = "fallback_full_frame"
    NONE = "none"


@dataclass(frozen=True)
class FrameSize:
    width: int
    height: int

    def area(self) -> int:
        return self.width * self.height

    def as_list(self) -> list[int]:
        return [self.width, self.height]


@dataclass(frozen=True)
class FramePacket:
    camera_id: str
    frame_id: int
    timestamp: float
    frame: Any
    original_size: FrameSize


@dataclass(frozen=True)
class ROI:
    x: int
    y: int
    w: int
    h: int
    score: float = 1.0
    coord_system: str = "original_frame"

    def area(self) -> int:
        return max(self.w, 0) * max(self.h, 0)

    def xywh(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]


@dataclass(frozen=True)
class ROIMetadata:
    camera_id: str
    frame_id: int
    timestamp: float
    roi_id: str
    original_frame_size: FrameSize
    analysis_frame_size: FrameSize
    roi: ROI
    source: str = "rule_based_roi_gate"
    trigger_type: TriggerType = TriggerType.ROI

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "roi_id": self.roi_id,
            "original_frame_size": self.original_frame_size.as_list(),
            "analysis_frame_size": self.analysis_frame_size.as_list(),
            "roi_xywh": self.roi.xywh(),
            "score": self.roi.score,
            "source": self.source,
            "trigger_type": self.trigger_type.value,
        }


@dataclass(frozen=True)
class Detection:
    camera_id: str
    frame_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]
    source: str
    roi_id: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentMetrics:
    frame_count: int = 0
    yolo_call_count: int = 0
    yolo_input_pixel_area: int = 0
    average_roi_count: float = 0.0
    average_roi_area_ratio: float = 0.0
    gate_latency_ms: list[float] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)
