"""Consistent UUIDv7 identifier generation across all domain entities and events."""

from __future__ import annotations

import os
import time
import uuid


def generate_uuidv7(prefix: str = "") -> str:
    """
    Generates an RFC 9562 time-ordered UUIDv7 identifier.
    Uses native uuid.uuid7() if available (Python 3.14+), or falls back to
    deterministic 48-bit millisecond timestamp + random bits format.
    """
    if hasattr(uuid, "uuid7"):
        raw = str(getattr(uuid, "uuid7")())
    else:
        ts_ms = int(time.time() * 1000)
        rand_bytes = os.urandom(10)
        b = bytearray(16)
        b[0:6] = ts_ms.to_bytes(6, "big")
        b[6:16] = rand_bytes
        b[6] = (b[6] & 0x0F) | 0x70  # Version 7
        b[8] = (b[8] & 0x3F) | 0x80  # Variant 10xx
        raw = str(uuid.UUID(bytes=bytes(b)))

    return f"{prefix}_{raw}" if prefix else raw
