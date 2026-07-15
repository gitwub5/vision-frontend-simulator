"""Frame stream loaders for videos and image sequences."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from time import time

from common import FramePacket, FrameSize


class DatasetStream:
    """Iterates dataset input as camera-like frame packets."""

    def __iter__(self) -> Iterator[FramePacket]:
        raise NotImplementedError


class VideoFrameStream(DatasetStream):
    def __init__(
        self,
        input_path: str | Path,
        camera_id: str = "cam_01",
        fps_override: float | None = None,
        frame_limit: int | None = None,
        start_frame: int = 0,
    ) -> None:
        self.input_path = Path(input_path)
        self.camera_id = camera_id
        self.fps_override = fps_override
        self.frame_limit = frame_limit
        self.start_frame = start_frame

    def __iter__(self) -> Iterator[FramePacket]:
        import cv2

        capture = cv2.VideoCapture(str(self.input_path))
        if not capture.isOpened():
            raise FileNotFoundError(f"Could not open video: {self.input_path}")

        fps = self.fps_override or capture.get(cv2.CAP_PROP_FPS) or 30.0
        capture.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

        emitted = 0
        frame_id = self.start_frame
        try:
            while self.frame_limit is None or emitted < self.frame_limit:
                ok, frame = capture.read()
                if not ok:
                    break

                height, width = frame.shape[:2]
                timestamp = frame_id / fps
                yield FramePacket(
                    camera_id=self.camera_id,
                    frame_id=frame_id,
                    timestamp=timestamp,
                    frame=frame,
                    original_size=FrameSize(width=width, height=height),
                )
                emitted += 1
                frame_id += 1
        finally:
            capture.release()


class ImageSequenceStream(DatasetStream):
    def __init__(
        self,
        input_path: str | Path,
        camera_id: str = "cam_01",
        fps: float = 30.0,
        extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp"),
        frame_limit: int | None = None,
    ) -> None:
        self.input_path = Path(input_path)
        self.camera_id = camera_id
        self.fps = fps
        self.extensions = tuple(ext.lower() for ext in extensions)
        self.frame_limit = frame_limit

    def __iter__(self) -> Iterator[FramePacket]:
        import cv2

        image_paths = sorted(
            path for path in self.input_path.iterdir() if path.suffix.lower() in self.extensions
        )
        if self.frame_limit is not None:
            image_paths = image_paths[: self.frame_limit]

        for frame_id, image_path in enumerate(image_paths):
            frame = cv2.imread(str(image_path))
            if frame is None:
                continue

            height, width = frame.shape[:2]
            yield FramePacket(
                camera_id=self.camera_id,
                frame_id=frame_id,
                timestamp=frame_id / self.fps if self.fps else time(),
                frame=frame,
                original_size=FrameSize(width=width, height=height),
            )
