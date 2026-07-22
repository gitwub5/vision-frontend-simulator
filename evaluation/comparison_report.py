"""Build comparison reports from full-frame and ROI-gated experiment outputs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from common import Detection
from evaluation.detection_metrics import DetectionMatchSummary, match_detections_by_iou
from evaluation.latency_metrics import LatencySummary, summarize_latency
from evaluation.roi_containment import RoiContainmentSummary, summarize_roi_containment
from evaluation.workload_metrics import WorkloadSummary, summarize_workload
from gpu_inference.yolo_roi import read_gate_frame_metadata_jsonl, read_roi_metadata_jsonl


@dataclass(frozen=True)
class ComparisonInputs:
    full_frame_detections: Path
    roi_detections: Path
    full_frame_metrics: Path
    roi_metrics: Path
    roi_metadata: Path
    frame_metadata: Path
    report_json: Path
    report_markdown: Path

    def to_json_dict(self) -> dict[str, str]:
        return {
            "full_frame_detections": str(self.full_frame_detections),
            "roi_detections": str(self.roi_detections),
            "full_frame_metrics": str(self.full_frame_metrics),
            "roi_metrics": str(self.roi_metrics),
            "roi_metadata": str(self.roi_metadata),
            "frame_metadata": str(self.frame_metadata),
            "report_json": str(self.report_json),
            "report_markdown": str(self.report_markdown),
        }


@dataclass(frozen=True)
class ComparisonReport:
    inputs: ComparisonInputs
    detection: DetectionMatchSummary
    roi: RoiContainmentSummary
    workload: WorkloadSummary
    latency: LatencySummary

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "inputs": self.inputs.to_json_dict(),
            "detection": self.detection.to_json_dict(),
            "roi": self.roi.to_json_dict(),
            "workload": self.workload.to_json_dict(),
            "latency": self.latency.to_json_dict(),
            "success_criteria": {
                "recall_retention_ge_0_95": self.detection.pseudo_recall >= 0.95,
                "roi_containment_rate_ge_0_98": self.roi.containment_rate >= 0.98,
                "input_pixel_area_reduction_ge_0_50": self.workload.input_pixel_area_reduction >= 0.5,
                "average_roi_count_le_3": self.roi.average_roi_count <= 3.0,
                "average_roi_area_ratio_le_0_30": self.roi.average_roi_area_ratio <= 0.30,
                "gate_average_latency_ms_le_10": self.latency.gate_average_latency_ms <= 10.0,
            },
        }

    def to_markdown(self) -> str:
        data = self.to_json_dict()
        success = data["success_criteria"]
        lines = [
            "# Phase 1 Comparison Report",
            "",
            "## Summary",
            "",
            f"- Pseudo recall retention: {_format_ratio(self.detection.pseudo_recall)}",
            f"- ROI containment rate: {_format_ratio(self.roi.containment_rate)}",
            f"- YOLO call reduction: {_format_ratio(self.workload.yolo_call_reduction)}",
            f"- YOLO input pixel area reduction: {_format_ratio(self.workload.input_pixel_area_reduction)}",
            f"- Average ROI count: {self.roi.average_roi_count:.3f}",
            f"- Average ROI area ratio: {_format_ratio(self.roi.average_roi_area_ratio)}",
            f"- Gate average latency: {self.latency.gate_average_latency_ms:.3f} ms",
            "",
            "## Detection",
            "",
            f"- Full-frame reference detections: {self.detection.reference_detection_count}",
            f"- ROI-gated detections: {self.detection.candidate_detection_count}",
            f"- Matched detections: {self.detection.matched_detection_count}",
            f"- IoU threshold: {self.detection.iou_threshold:.2f}",
            "",
            "## Workload",
            "",
            f"- Full-frame YOLO calls: {self.workload.full_frame_yolo_call_count}",
            f"- ROI-gated YOLO calls: {self.workload.roi_yolo_call_count}",
            f"- Full-frame input pixel area: {self.workload.full_frame_input_pixel_area}",
            f"- ROI-gated input pixel area: {self.workload.roi_input_pixel_area}",
            "",
            "## Latency",
            "",
            f"- Full-frame average YOLO latency: {self.latency.full_frame_average_latency_ms:.3f} ms",
            f"- ROI-gated average YOLO latency: {self.latency.roi_average_latency_ms:.3f} ms",
            f"- Gate max latency: {self.latency.gate_max_latency_ms:.3f} ms",
            "",
            "## Success Criteria",
            "",
        ]
        for key, value in success.items():
            lines.append(f"- {key}: {'PASS' if value else 'FAIL'}")
        lines.extend(
            [
                "",
                "## Inputs",
                "",
            ]
        )
        for key, value in self.inputs.to_json_dict().items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
        return "\n".join(lines)


def build_comparison_report(inputs: ComparisonInputs, iou_threshold: float = 0.5) -> ComparisonReport:
    full_frame_detections = read_detection_jsonl(inputs.full_frame_detections)
    roi_detections = read_detection_jsonl(inputs.roi_detections)
    full_frame_metrics = read_json(inputs.full_frame_metrics)
    roi_metrics = read_json(inputs.roi_metrics)
    roi_records = read_roi_metadata_jsonl(inputs.roi_metadata)
    frame_records = read_gate_frame_metadata_jsonl(inputs.frame_metadata)

    detection = match_detections_by_iou(full_frame_detections, roi_detections, iou_threshold)
    roi = summarize_roi_containment(full_frame_detections, roi_records, frame_records)
    workload = summarize_workload(full_frame_metrics, roi_metrics)
    latency = summarize_latency(full_frame_metrics, roi_metrics, frame_records)

    return ComparisonReport(
        inputs=inputs,
        detection=detection,
        roi=roi,
        workload=workload,
        latency=latency,
    )


def read_detection_jsonl(input_path: str | Path) -> list[Detection]:
    detections: list[Detection] = []
    for data in read_jsonl(input_path):
        detections.append(
            Detection(
                camera_id=str(data["camera_id"]),
                frame_id=int(data["frame_id"]),
                class_id=int(data["class_id"]),
                class_name=str(data["class_name"]),
                confidence=float(data["confidence"]),
                bbox_xyxy=[float(value) for value in data["bbox_xyxy"]],
                source=str(data["source"]),
                roi_id=data.get("roi_id"),
            )
        )
    return detections


def read_json(input_path: str | Path) -> dict[str, Any]:
    with Path(input_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def read_jsonl(input_path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(input_path).open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def write_report_json(report: ComparisonReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report.to_json_dict(), file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_report_markdown(report: ComparisonReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_markdown(), encoding="utf-8")


def _format_ratio(value: float) -> str:
    return f"{value:.3f} ({value * 100:.1f}%)"
