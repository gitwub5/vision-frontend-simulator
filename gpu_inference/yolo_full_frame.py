"""Full-frame YOLO baseline entry point."""

from __future__ import annotations

from collections.abc import Iterable

from common import Detection, FramePacket


class FullFrameYoloRunner:
    def __init__(self, model_path: str, image_size: int = 640) -> None:
        self.model_path = model_path
        self.image_size = image_size
        self._model = None

    def load(self):
        from ultralytics import YOLO

        self._model = YOLO(self.model_path)
        return self

    def run(self, frames: Iterable[FramePacket]) -> list[Detection]:
        if self._model is None:
            self.load()
        raise NotImplementedError("Full-frame YOLO result conversion will be implemented in Task 5.")
