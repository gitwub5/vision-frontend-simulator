"""Rule-based NPX/Vision Frontend Gate emulator."""

from npx_emulator.gate import (
    GateDecision,
    NpxGateConfig,
    RuleBasedNpxGate,
    is_periodic_full_frame,
    load_npx_gate_config,
    should_fallback_to_full_frame,
)
from npx_emulator.metadata import (
    GateFrameMetadataWriter,
    ROIMetadataWriter,
    build_roi_id,
    frame_metadata_from_gate_decision,
    roi_metadata_from_gate_decision,
)

__all__ = [
    "GateDecision",
    "NpxGateConfig",
    "RuleBasedNpxGate",
    "is_periodic_full_frame",
    "load_npx_gate_config",
    "should_fallback_to_full_frame",
    "GateFrameMetadataWriter",
    "ROIMetadataWriter",
    "build_roi_id",
    "frame_metadata_from_gate_decision",
    "roi_metadata_from_gate_decision",
]
