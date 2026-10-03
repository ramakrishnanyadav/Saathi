"""Simulated clock adapter with time travel support for tests and interactive demo scrubber."""

from __future__ import annotations


class SimClock:
    """Controllable clock for time-travel, testing, and demo scrubbers."""

    def __init__(self, initial_ms: int = 1_700_000_000_000) -> None:
        self._current_ms = initial_ms

    def now_ms(self) -> int:
        return self._current_ms

    def advance_ms(self, delta_ms: int) -> int:
        """Advances current time by delta_ms and returns the new timestamp."""
        if delta_ms < 0:
            raise ValueError("Time travel backwards is disallowed.")
        self._current_ms += delta_ms
        return self._current_ms

    def set_time(self, timestamp_ms: int) -> None:
        """Sets the clock explicitly to timestamp_ms."""
        self._current_ms = timestamp_ms
