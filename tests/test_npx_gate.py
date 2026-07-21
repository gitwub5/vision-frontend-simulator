from __future__ import annotations

import unittest
from unittest.mock import patch

from common import FramePacket, FrameSize, ROI, TriggerType
from npx_emulator.gate import (
    NpxGateConfig,
    RuleBasedNpxGate,
    is_periodic_full_frame,
    should_fallback_to_full_frame,
)
from npx_emulator.temporal_hold import TemporalHold


class FakeGrayFrame:
    pass


class FakeEventMaps:
    motion_map = object()


class RuleBasedNpxGateTest(unittest.TestCase):
    def test_first_frame_triggers_full_frame_check(self) -> None:
        gate = RuleBasedNpxGate(NpxGateConfig(full_frame_interval=60))
        packet = _packet(frame_id=0)

        with _patched_gate_helpers(rois=[]):
            decision = gate.process(packet)

        self.assertEqual(decision.trigger_type, TriggerType.FULL_FRAME)
        self.assertTrue(decision.should_run_full_frame)
        self.assertEqual(decision.rois, [])

    def test_motion_roi_triggers_roi_decision(self) -> None:
        gate = RuleBasedNpxGate(NpxGateConfig(full_frame_interval=60))

        with _patched_gate_helpers(rois=[ROI(x=10, y=10, w=20, h=20, coord_system="analysis_frame")]):
            gate.process(_packet(frame_id=0))
            decision = gate.process(_packet(frame_id=1))

        self.assertEqual(decision.trigger_type, TriggerType.ROI)
        self.assertFalse(decision.should_run_full_frame)
        self.assertEqual(len(decision.rois), 1)
        self.assertEqual(decision.rois[0].coord_system, "original_frame")
        self.assertGreater(decision.rois[0].w, 0)
        self.assertGreater(decision.rois[0].h, 0)

    def test_temporal_hold_triggers_when_motion_disappears(self) -> None:
        gate = RuleBasedNpxGate(NpxGateConfig(hold_frames=2, full_frame_interval=60))

        with _patched_gate_helpers(rois=[ROI(x=10, y=10, w=20, h=20, coord_system="analysis_frame")]):
            gate.process(_packet(frame_id=0))
            first_motion = gate.process(_packet(frame_id=1))

        with _patched_gate_helpers(rois=[]):
            held = gate.process(_packet(frame_id=2))

        self.assertEqual(first_motion.trigger_type, TriggerType.ROI)
        self.assertEqual(held.trigger_type, TriggerType.HOLD)
        self.assertEqual(len(held.rois), 1)

    def test_periodic_full_frame_preserves_rois(self) -> None:
        gate = RuleBasedNpxGate(NpxGateConfig(full_frame_interval=2))

        with _patched_gate_helpers(rois=[ROI(x=5, y=5, w=8, h=8, coord_system="analysis_frame")]):
            gate.process(_packet(frame_id=0))
            gate.process(_packet(frame_id=1))
            decision = gate.process(_packet(frame_id=2))

        self.assertEqual(decision.trigger_type, TriggerType.FULL_FRAME)
        self.assertTrue(decision.should_run_full_frame)
        self.assertEqual(len(decision.rois), 1)

    def test_excessive_roi_area_falls_back_to_full_frame(self) -> None:
        gate = RuleBasedNpxGate(
            NpxGateConfig(full_frame_interval=60, max_total_roi_area_ratio=0.1, margin_ratio=0.0)
        )

        with _patched_gate_helpers(rois=[ROI(x=0, y=0, w=80, h=80, coord_system="analysis_frame")]):
            gate.process(_packet(frame_id=0))
            decision = gate.process(_packet(frame_id=1))

        self.assertEqual(decision.trigger_type, TriggerType.FALLBACK_FULL_FRAME)
        self.assertTrue(decision.should_run_full_frame)
        self.assertEqual(decision.rois, [])


class GatePolicyTest(unittest.TestCase):
    def test_should_fallback_when_roi_count_exceeds_limit(self) -> None:
        config = NpxGateConfig(max_roi_per_frame=1)
        rois = [ROI(0, 0, 10, 10), ROI(20, 20, 10, 10)]
        self.assertTrue(should_fallback_to_full_frame(rois, FrameSize(100, 100), config))

    def test_should_fallback_when_roi_area_exceeds_limit(self) -> None:
        config = NpxGateConfig(max_total_roi_area_ratio=0.25)
        rois = [ROI(0, 0, 60, 60)]
        self.assertTrue(should_fallback_to_full_frame(rois, FrameSize(100, 100), config))

    def test_periodic_full_frame_skips_first_frame_policy(self) -> None:
        self.assertFalse(is_periodic_full_frame(frame_id=0, interval=30))
        self.assertFalse(is_periodic_full_frame(frame_id=29, interval=30))
        self.assertTrue(is_periodic_full_frame(frame_id=30, interval=30))

    def test_temporal_hold_expires(self) -> None:
        hold = TemporalHold(hold_frames=2)
        roi = ROI(1, 2, 3, 4)

        self.assertEqual(hold.update([roi]), [roi])
        self.assertEqual(hold.update([]), [roi])
        self.assertEqual(hold.update([]), [])


def _packet(frame_id: int) -> FramePacket:
    return FramePacket(
        camera_id="cam_test",
        frame_id=frame_id,
        timestamp=float(frame_id) / 30.0,
        frame=object(),
        original_size=FrameSize(width=100, height=100),
    )


def _patched_gate_helpers(rois: list[ROI]):
    return patch.multiple(
        "npx_emulator.gate",
        to_gray=lambda frame: FakeGrayFrame(),
        resize_for_analysis=lambda gray, analysis_size: FakeGrayFrame(),
        encode_event_maps=lambda **kwargs: FakeEventMaps(),
        filter_motion_map=lambda motion_map, kernel_size: motion_map,
        generate_roi_candidates=lambda motion_map, min_area_ratio: rois,
    )


if __name__ == "__main__":
    unittest.main()
