"""Clock protocol for injected deterministic time."""

from __future__ import annotations

from typing import Protocol


class Clock(Protocol):
    """Protocol for reading the current time in UTC epoch milliseconds."""

    def now_ms(self) -> int:
        """Returns the current UTC epoch time in milliseconds."""
        ...
