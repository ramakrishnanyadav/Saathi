"""System clock adapter implementation of Clock protocol."""

from __future__ import annotations

import time


class SystemClock:
    """Reads system wall clock in UTC epoch milliseconds."""

    def now_ms(self) -> int:
        return int(time.time() * 1000)
