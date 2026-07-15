"""ROI metadata serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path

from common import ROIMetadata


class ROIMetadataWriter:
    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write_all(self, records: list[ROIMetadata]) -> None:
        with self.output_path.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record.to_json_dict(), ensure_ascii=False) + "\n")
