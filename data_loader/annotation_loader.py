"""Annotation loader extension point.

Phase 1 can use full-frame YOLO output as a pseudo baseline. Dataset-specific
annotation parsing will be added when OD-VIRAT/VIRAT annotations are selected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class AnnotationLoader:
    def __init__(self, input_path: str | Path | None = None) -> None:
        self.input_path = Path(input_path) if input_path else None

    def load(self) -> dict[int, list[dict[str, Any]]]:
        if self.input_path is None:
            return {}
        raise NotImplementedError("Dataset-specific annotation loading is not implemented yet.")
