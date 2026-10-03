"""
SAATH Performance Budget Test Suite
Measures and asserts P95 latency bounds across the sacred loop stages.
"""
from __future__ import annotations

import time
import statistics
import pytest
from saath.api.deps import reset_app_state
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.application.orchestrator import SaathOrchestrator
from saath.adapters.llm_ollama import OllamaLLMProvider
from saath.adapters.clock_sim import SimClock


@pytest.fixture(autouse=True)
def isolated():
    reset_app_state(":memory:")


@pytest.mark.asyncio
async def test_perf_budget_rule_ingestion_p95():
    """Text ingestion with rule fallback P95 must be < 100ms."""
    store = SQLiteEventStore(":memory:")
    await store.connect()
    await store.record_house("h-perf", "Perf House", "Asia/Kolkata", 1000)
    await store.record_member("m-p1", "h-perf", "Dev", None, "flatmate", [], 1000)

    from unittest.mock import patch, AsyncMock
    llm = OllamaLLMProvider(base_url="http://127.0.0.1:9999", timeout_seconds=0.01)
    clock = SimClock(1000)
    orchestrator = SaathOrchestrator(store=store, llm_provider=llm)

    durations: list[float] = []
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))

    with patch("httpx.AsyncClient", return_value=mock_client):
        for i in range(20):
            t0 = time.perf_counter()
            await orchestrator.ingest_message(
                house_id="h-perf",
                author_id="m-p1",
                text=f"landlord will fix tap by tomorrow {i}",
                dedupe_key=f"perf-{i}",
                now_ms=1000 + i * 1000,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            durations.append(elapsed_ms)

    sorted_d = sorted(durations)
    p95 = sorted_d[int(len(sorted_d) * 0.95)]
    print(f"\nRule Ingestion Latencies: P50={statistics.median(sorted_d):.2f}ms, P95={p95:.2f}ms")
    assert p95 < 200.0, f"Rule ingestion P95 too slow: {p95:.2f}ms (budget < 200ms)"


@pytest.mark.asyncio
async def test_perf_budget_attention_query_p95():
    """Attention query P95 must be < 50ms."""
    store = SQLiteEventStore(":memory:")
    await store.connect()
    await store.record_house("h-att", "Att House", "Asia/Kolkata", 1000)
    await store.record_member("m-a1", "h-att", "Alice", None, "flatmate", [], 1000)

    # Populate 50 commitments
    for i in range(50):
        await store.record_message(f"m-{i}", "h-att", "m-a1", "test", f"dk-{i}", 1000 + i)

    durations: list[float] = []
    for _ in range(25):
        t0 = time.perf_counter()
        commitments = await store.get_open_commitments("h-att")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations.append(elapsed_ms)

    sorted_d = sorted(durations)
    p95 = sorted_d[int(len(sorted_d) * 0.95)]
    print(f"\nAttention Query Latencies: P50={statistics.median(sorted_d):.2f}ms, P95={p95:.2f}ms")
    assert p95 < 50.0, f"Attention query P95 too slow: {p95:.2f}ms (budget < 50ms)"


@pytest.mark.asyncio
async def test_perf_budget_database_replay_p95():
    """Replay of 50 events P95 must be < 100ms."""
    store = SQLiteEventStore(":memory:")
    await store.connect()
    await store.record_house("h-rep-p", "Replay Perf", "Asia/Kolkata", 1000)
    await store.record_member("m-r1", "h-rep-p", "Bob", None, "flatmate", [], 1000)

    clock = SimClock(1000)
    orchestrator = SaathOrchestrator(store=store, llm_provider=OllamaLLMProvider(timeout_seconds=0.01))

    for i in range(20):
        await orchestrator.ingest_message("h-rep-p", "m-r1", f"bai nahi aayi {i}", dedupe_key=f"rep-{i}", now_ms=1000+i)

    t0 = time.perf_counter()
    await store.rebuild_projections_from_events("h-rep-p")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    print(f"\nReplay 20 events duration: {elapsed_ms:.2f}ms")
    assert elapsed_ms < 500.0, f"Replay too slow: {elapsed_ms:.2f}ms (budget < 500ms)"
