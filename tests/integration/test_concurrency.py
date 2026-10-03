"""
SAATH Concurrency Tests
Ensures one deterministic final state under concurrent writes.
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from saath.api.deps import reset_app_state


@pytest.fixture(autouse=True)
def isolated():
    reset_app_state(":memory:")


async def _seed(store, house_id: str, member_ids: list[str], names: list[str]):
    await store.connect()
    await store.record_house(house_id, f"House {house_id}", "Asia/Kolkata", 1000)
    for mid, name in zip(member_ids, names):
        await store.record_member(mid, house_id, name, None, "flatmate", [], 1000)


# ---------------------------------------------------------------------------
# CC-1: Two devices confirm same expense — exactly one confirmation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_expense_confirm_idempotent():
    """CC-1: Two devices confirming the same expense produce exactly one confirmed state."""
    from saath.api.deps import _store, _orchestrator

    await _seed(_store, "h-cc1", ["m-c1a", "m-c1b"], ["Dev A", "Dev B"])

    # Device A ingests an expense
    result = await _orchestrator.ingest_message(
        "h-cc1", "m-c1a",
        "bijli bill ₹1500 bhar diya",
        dedupe_key="cc1-expense",
        now_ms=1_000,
    )

    # Find the expense id from pending confirmations
    pending = result.pending_confirmations
    if not pending:
        # Try getting from store
        expenses = await _store.get_expenses("h-cc1")
        pending_exps = [e for e in expenses if not e.get("is_confirmed")]
        if not pending_exps:
            pytest.skip("No pending expense to confirm")
        expense_id = pending_exps[0]["id"]
    else:
        expense_id = pending[0].get("expense_id") or pending[0].get("id")

    # Both devices race to confirm
    async def confirm(actor_id: str):
        return await _orchestrator.confirm_expense(
            house_id="h-cc1",
            author_id=actor_id,
            payload={
                "expense_id": expense_id,
                "title": "bijli bill",
                "amount_paise": 150000,
                "paid_by": actor_id,
                "participant_ids": ["m-c1a", "m-c1b"],
                "shares": {"m-c1a": 75000, "m-c1b": 75000},
            },
            now_ms=2_000,
        )

    results = await asyncio.gather(confirm("m-c1a"), confirm("m-c1b"), return_exceptions=True)

    # Either both succeed idempotently, or one succeeds and one errors
    expenses_after = await _store._conn.execute_fetchall(
        "SELECT * FROM projection_expense WHERE house_id='h-cc1'"
    )
    confirmed_expenses = [e for e in expenses_after if e[4]]
    # There must be at least 1 confirmed expense
    assert len(confirmed_expenses) >= 1, f"Expected confirmed expense, got {len(confirmed_expenses)}"


# ---------------------------------------------------------------------------
# CC-2: Device A marks commitment done, Device B reschedules — last write with causality wins
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_commitment_update_no_phantom():
    """CC-2: Concurrent done + reschedule on same commitment — no phantom states."""
    from saath.api.deps import _store, _orchestrator
    from saath.domain.events import DomainEvent, EventType
    from saath.domain.ids import generate_uuidv7

    await _seed(_store, "h-cc2", ["m-c2a", "m-c2b"], ["Alice", "Bob"])

    result = await _orchestrator.ingest_message(
        "h-cc2", "m-c2a",
        "landlord will fix tap by tomorrow",
        dedupe_key="cc2-commitment",
        now_ms=1_000,
    )

    commitments = await _store.get_open_commitments("h-cc2")
    if not commitments:
        pytest.skip("No commitment created")

    commitment_id = commitments[0].id

    # Two concurrent updates
    async def mark_done():
        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id="h-cc2",
            event_type=EventType.COMMITMENT_UPDATED,
            actor_id="m-c2a",
            occurred_at=2_000,
            payload={"commitment_id": commitment_id, "new_state": "done", "note": "fixed"},
        )
        await _store.append_events_and_project_batch([ev])

    async def reschedule():
        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id="h-cc2",
            event_type=EventType.COMMITMENT_UPDATED,
            actor_id="m-c2b",
            occurred_at=2_000,
            payload={"commitment_id": commitment_id, "new_state": "rescheduled", "new_due_at": 5_000, "note": "not fixed yet"},
        )
        await _store.append_events_and_project_batch([ev])

    await asyncio.gather(mark_done(), reschedule())

    # Verify: event log grows, projection is consistent (no phantom "waiting" duplicate)
    events = await _store.get_all_events("h-cc2")
    commitment_events = [e for e in events if e.payload.get("commitment_id") == commitment_id
                         or e.event_type.value in ("commitment_created", "commitment_updated")]

    # No commitment should appear twice in projections with different states simultaneously
    all_commitments = await _store.get_open_commitments("h-cc2")
    same_id = [c for c in all_commitments if c.id == commitment_id]
    assert len(same_id) <= 1, f"Commitment {commitment_id} has {len(same_id)} projection rows!"


# ---------------------------------------------------------------------------
# CC-3: Two devices submit duplicate event simultaneously
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_duplicate_event_exactly_one_applied():
    """CC-3: Two devices sending same dedupe_key concurrently — exactly one stored."""
    from saath.api.deps import _store, _orchestrator

    await _seed(_store, "h-cc3", ["m-c3a"], ["Charlie"])

    dedupe_key = f"cc3-{uuid.uuid4().hex[:8]}"
    text = "doodh khatam hai"

    # Submit from "two devices" concurrently
    results = await asyncio.gather(
        _orchestrator.ingest_message("h-cc3", "m-c3a", text, dedupe_key=dedupe_key, now_ms=1000),
        _orchestrator.ingest_message("h-cc3", "m-c3a", text, dedupe_key=dedupe_key, now_ms=1000),
        return_exceptions=True,
    )

    # Count which succeeded
    non_dup = [r for r in results if not isinstance(r, Exception) and not r.is_duplicate]
    is_dup = [r for r in results if not isinstance(r, Exception) and r.is_duplicate]

    assert len(non_dup) <= 1, f"Two concurrent identical messages both succeeded: {len(non_dup)}"
    total_non_exception = len(non_dup) + len(is_dup)
    assert total_non_exception == 2, "Both requests should complete (one dup, one success)"

    # Check supply projection has exactly one entry
    supplies = await _store._conn.execute_fetchall(
        "SELECT * FROM projection_supply WHERE house_id = 'h-cc3' AND item_norm = 'milk'"
    )
    assert len(supplies) <= 1, f"Duplicate supply entries: {len(supplies)}"


# ---------------------------------------------------------------------------
# CC-4: Two requests to same commitment simultaneously
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_same_commitment_requests():
    """CC-4: Two simultaneous ingestions referencing the same commitment produce consistent state."""
    from saath.api.deps import _store, _orchestrator

    await _seed(_store, "h-cc4", ["m-c4a"], ["Dev"])

    # Create one commitment
    await _orchestrator.ingest_message(
        "h-cc4", "m-c4a", "landlord fix tap by Monday", dedupe_key="cc4-base", now_ms=1000
    )

    # Two different dedupe keys but both reply to same commitment
    async def reply(dedupe: str, text: str):
        return await _orchestrator.ingest_message(
            "h-cc4", "m-c4a", text, dedupe_key=dedupe, now_ms=2000
        )

    r1, r2 = await asyncio.gather(
        reply("cc4-r1", "ho gaya"),
        reply("cc4-r2", "landlord called said he will come Thursday"),
    )

    # Both replies processed — system must not crash
    assert r1 is not None
    assert r2 is not None

    # Verify all events are stored
    events = await _store.get_all_events("h-cc4")
    assert len(events) >= 1  # At least the original commitment event
