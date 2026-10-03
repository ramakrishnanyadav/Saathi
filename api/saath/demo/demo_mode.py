"""
SAATH Demo Determinism Mode

DEMO_MODE provides:
- Fixed clock (no wall-clock drift)
- Seeded household with known members
- Deterministic IDs (UUIDv5 from seed rather than UUIDv7)
- Known sample data for all scenarios
- Time travel via /demo/advance-clock
- Reset button via /demo/reset

Usage:
  SAATH_DEMO=1 uvicorn saath.api.main:app
  or set demo=true in settings

All demo responses are stable and reproducible every single time.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

DEMO_HOUSE_ID = "h-demo"
DEMO_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

# Fixed demo clock: 2024-10-03 07:00:00 IST = 1727910600000 ms UTC
DEMO_BASE_MS = 1_727_910_600_000

# Demo members (stable, non-hardcoded identities — just for demo mode)
DEMO_MEMBERS = [
    {"id": "m-1", "name": "You", "phone": None, "role": "flatmate", "aliases": ["me", "mujhe"]},
    {"id": "m-2", "name": "Rahul", "phone": "+919876543210", "role": "flatmate", "aliases": ["rahul"]},
    {"id": "m-3", "name": "Amit", "phone": "+919876543211", "role": "flatmate", "aliases": ["amit"]},
]

# Demo scenarios — ordered for predictable walkthrough
DEMO_SCENARIOS = [
    {
        "id": "demo-s1",
        "label": "Landlord commits to fix tap",
        "text": "landlord bola kal tap theek karne aadmi bhejega",
        "dedupe_key": "demo-s1-tap",
        "expected": "commitment_created",
    },
    {
        "id": "demo-s2",
        "label": "Milk runs out",
        "text": "doodh khatam hai",
        "dedupe_key": "demo-s2-milk",
        "expected": "supply_depleted",
    },
    {
        "id": "demo-s3",
        "label": "Maid didn't come today",
        "text": "bai aaj nahi aayi",
        "dedupe_key": "demo-s3-maid",
        "expected": "action_taken",
    },
    {
        "id": "demo-s4",
        "label": "Split electricity bill",
        "text": "bijli bill 1450 bhar diya, teen mein split karo",
        "dedupe_key": "demo-s4-bill",
        "expected": "expense_created (pending confirmation)",
    },
    {
        "id": "demo-s5",
        "label": "Landlord overdue → follow-up ready",
        "text": "ho gaya tap ka?",
        "dedupe_key": "demo-s5-fu",
        "expected": "ask_which or followup",
        "requires_clock_advance_hours": 30,  # advance past due date
    },
]


def make_demo_id(seed: str, prefix: str = "demo") -> str:
    """Deterministic UUIDv5-based ID from seed (for demo reproducibility)."""
    uid = uuid.uuid5(DEMO_NAMESPACE, f"{prefix}:{seed}")
    return f"{prefix}-{str(uid).replace('-', '')[:12]}"


@dataclass(frozen=True)
class DemoState:
    """Represents current demo mode state."""
    is_demo: bool
    clock_offset_ms: int = 0
    current_scenario_idx: int = 0

    @property
    def current_time_ms(self) -> int:
        return DEMO_BASE_MS + self.clock_offset_ms

    @property
    def current_scenario(self) -> dict | None:
        if 0 <= self.current_scenario_idx < len(DEMO_SCENARIOS):
            return DEMO_SCENARIOS[self.current_scenario_idx]
        return None


# Module-level demo state
_demo_state = DemoState(is_demo=False)


def enable_demo_mode() -> DemoState:
    global _demo_state
    _demo_state = DemoState(is_demo=True, clock_offset_ms=0, current_scenario_idx=0)
    return _demo_state


def get_demo_state() -> DemoState:
    return _demo_state


def advance_demo_clock(hours: float) -> DemoState:
    global _demo_state
    _demo_state = DemoState(
        is_demo=_demo_state.is_demo,
        clock_offset_ms=_demo_state.clock_offset_ms + int(hours * 3_600_000),
        current_scenario_idx=_demo_state.current_scenario_idx,
    )
    return _demo_state


def advance_demo_scenario() -> DemoState:
    global _demo_state
    _demo_state = DemoState(
        is_demo=_demo_state.is_demo,
        clock_offset_ms=_demo_state.clock_offset_ms,
        current_scenario_idx=_demo_state.current_scenario_idx + 1,
    )
    return _demo_state


def reset_demo() -> DemoState:
    global _demo_state
    _demo_state = DemoState(is_demo=True, clock_offset_ms=0, current_scenario_idx=0)
    return _demo_state


def is_demo_mode() -> bool:
    import os
    return _demo_state.is_demo or os.environ.get("SAATH_DEMO", "").lower() in ("1", "true", "yes")
