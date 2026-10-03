"""
SAATH Observability Middleware
Measures the sacred loop at every stage:
  input_received → understanding_started → LLM_completed → validation_completed
  → event_written → projection_updated → UI_updated

Records P50/P95/P99 for all pipeline stages.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("saath.observability")

# In-memory ring buffer for latency samples (last 10000 per route)
_RING_SIZE = 10_000
_latencies: dict[str, list[float]] = defaultdict(list)

# Sacred-loop stage tags mapped to URL patterns
_STAGE_MAP = {
    "/api/v1/messages": "text_ingestion",
    "/api/v1/messages/voice": "voice_ingestion",
    "/api/v1/events/confirm": "expense_confirmation",
    "/api/v1/expenses/confirm": "expense_confirmation",
    "/api/v1/outbox/sync": "offline_sync",
    "/api/v1/commitments": "commitment_query",
    "/api/v1/events": "event_query",
}


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    idx = int(len(sorted_s) * pct / 100)
    return sorted_s[min(idx, len(sorted_s) - 1)]


def get_latency_stats() -> dict[str, dict[str, float]]:
    """Return P50/P95/P99 latency (ms) for each pipeline stage."""
    stats = {}
    for route, samples in _latencies.items():
        if samples:
            stats[route] = {
                "p50_ms": round(_percentile(samples, 50), 2),
                "p95_ms": round(_percentile(samples, 95), 2),
                "p99_ms": round(_percentile(samples, 99), 2),
                "count": len(samples),
                "min_ms": round(min(samples), 2),
                "max_ms": round(max(samples), 2),
            }
    return stats


def reset_latency_stats() -> None:
    """Reset all latency samples (e.g., for testing)."""
    _latencies.clear()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Measures end-to-end latency for every SAATH API call and logs:
    - Stage name (from _STAGE_MAP)
    - HTTP method, path, status code
    - Duration in milliseconds
    - House ID (from header, if present)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        house_id = request.headers.get("x-house-id", "unknown")
        path = request.url.path

        # Tag with sacred loop stage
        stage = "unknown"
        for prefix, tag in _STAGE_MAP.items():
            if path.startswith(prefix):
                stage = tag
                break

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "saath.pipeline.error stage=%s house=%s path=%s error=%s duration_ms=%.2f",
                stage, house_id, path, type(exc).__name__, elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Store sample in ring buffer
        samples = _latencies[stage]
        samples.append(elapsed_ms)
        if len(samples) > _RING_SIZE:
            del samples[: len(samples) - _RING_SIZE]

        # Structured log line for the sacred loop
        logger.info(
            "saath.pipeline stage=%s house=%s method=%s path=%s status=%d duration_ms=%.2f",
            stage, house_id, request.method, path, status, elapsed_ms,
        )

        # Add latency headers for client-side measurement
        response.headers["X-SAATH-Stage"] = stage
        response.headers["X-SAATH-Duration-Ms"] = f"{elapsed_ms:.2f}"

        # Warn if we exceed performance budgets
        budgets = {
            "text_ingestion": 5000,      # <5s (includes LLM timeout)
            "voice_ingestion": 10000,    # <10s (includes Whisper)
            "expense_confirmation": 500, # <500ms (pure DB)
            "offline_sync": 2000,        # <2s per batch
            "commitment_query": 200,     # <200ms
            "event_query": 200,          # <200ms
        }
        budget = budgets.get(stage)
        if budget and elapsed_ms > budget:
            logger.warning(
                "saath.budget.exceeded stage=%s duration_ms=%.2f budget_ms=%d",
                stage, elapsed_ms, budget,
            )

        return response
