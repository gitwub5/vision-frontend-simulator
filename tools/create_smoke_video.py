"""Create a deterministic fixed-camera smoke-test video.

The generated video is intentionally synthetic. It is for pipeline smoke tests,
not for detection-quality validation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a fixed-camera synthetic smoke-test video.")
    parser.add_argument("--output", default="data/smoke/fixed_camera_motion.mp4", help="Output video path.")
    parser.add_argument("--width", type=int, default=640, help="Video width.")
    parser.add_argument("--height", type=int, default=360, help="Video height.")
    parser.add_argument("--fps", type=float, default=30.0, help="Frames per second.")
    parser.add_argument("--frames", type=int, default=180, help="Number of frames to generate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cv2, np = _load_dependencies()
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        args.fps,
        (args.width, args.height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer: {output_path}")

    try:
        for frame_id in range(args.frames):
            writer.write(_render_frame(cv2, np, frame_id, args.width, args.height))
    finally:
        writer.release()

    print(
        {
            "output": str(output_path),
            "frames": args.frames,
            "fps": args.fps,
            "size": [args.width, args.height],
        }
    )


def _render_frame(cv2, np, frame_id: int, width: int, height: int):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (38, 42, 45)

    # Fixed-camera background: lanes, loading bay, and static objects.
    cv2.rectangle(frame, (0, height - 90), (width, height), (62, 67, 70), -1)
    cv2.line(frame, (0, height - 95), (width, height - 95), (92, 95, 96), 2)
    for x in range(60, width, 120):
        cv2.line(frame, (x, height - 88), (x + 45, height - 88), (170, 170, 155), 3)
    cv2.rectangle(frame, (40, 45), (180, 120), (78, 82, 84), -1)
    cv2.rectangle(frame, (460, 55), (585, 145), (70, 74, 77), -1)
    cv2.circle(frame, (530, 210), 32, (55, 60, 58), -1)

    # Moving vehicle-like object with a short stop interval to exercise temporal hold.
    if frame_id < 65:
        car_x = 40 + frame_id * 4
    elif frame_id < 95:
        car_x = 300
    else:
        car_x = 300 + (frame_id - 95) * 3
    car_x = min(car_x, width - 110)
    car_y = height - 72
    cv2.rectangle(frame, (car_x, car_y), (car_x + 82, car_y + 34), (36, 145, 214), -1)
    cv2.circle(frame, (car_x + 18, car_y + 34), 8, (18, 22, 24), -1)
    cv2.circle(frame, (car_x + 64, car_y + 34), 8, (18, 22, 24), -1)

    # Moving person-like object in a different region.
    person_x = 520 - min(frame_id, 120) * 2
    person_y = 170
    cv2.circle(frame, (person_x, person_y), 9, (230, 220, 190), -1)
    cv2.rectangle(frame, (person_x - 7, person_y + 9), (person_x + 7, person_y + 39), (190, 88, 78), -1)

    # Deterministic mild sensor noise.
    rng = np.random.default_rng(seed=frame_id)
    noise = rng.integers(0, 4, size=frame.shape, dtype=np.uint8)
    return cv2.add(frame, noise)


def _load_dependencies():
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "OpenCV and NumPy are required to create the smoke video. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc
    return cv2, np


if __name__ == "__main__":
    main()
