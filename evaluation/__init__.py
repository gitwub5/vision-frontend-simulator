"""Evaluation metric helpers."""

from evaluation.comparison_report import (
    ComparisonInputs,
    ComparisonReport,
    build_comparison_report,
    read_detection_jsonl,
    write_report_json,
    write_report_markdown,
)

__all__ = [
    "ComparisonInputs",
    "ComparisonReport",
    "build_comparison_report",
    "read_detection_jsonl",
    "write_report_json",
    "write_report_markdown",
]
