"""Rule-based NPX/Vision Frontend Gate emulator."""

from npx_emulator.gate import (
    GateDecision,
    NpxGateConfig,
    RuleBasedNpxGate,
    is_periodic_full_frame,
    load_npx_gate_config,
    should_fallback_to_full_frame,
)

__all__ = [
    "GateDecision",
    "NpxGateConfig",
    "RuleBasedNpxGate",
    "is_periodic_full_frame",
    "load_npx_gate_config",
    "should_fallback_to_full_frame",
]
