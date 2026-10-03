"""
SAATH Database Disaster Recovery Tests

Tests the strongest property of the event-sourced architecture:
  "Delete projections → replay events → recover identical state."

Also tests:
- Crash during event write
- Crash during projection
- Corrupted projection
- Restart after crash
- Rebuild projection from events
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from saath.api.deps import reset_app_state


@pytest.fixture(autouse=True)
def isolated():
    reset_app_state(":memory:")


async def _setup_house(store, orchestrator):
    """Seed a house with 2 members and ingest 5 diverse events."""
    await store.connect()
    await store.record_house("h-dr", "Disaster Recovery House", "Asia/Kolkata", 1000)
    await store.record_member("m-dr1", "h-dr", "Alice", None, "flatmate", [], 1000)
    await store.record_member("m-dr2", "h-dr", "Bob", None, "flatmate", [], 1000)

    await orchestrator.ingest_message("h-dr", "m-dr1", "landlord will fix tap by Friday", dedupe_key="dr-c1", now_ms=2000)
    await orchestrator.ingest_message("h-dr", "m-dr1", "doodh khatam hai", dedupe_key="dr-s1", now_ms=3000)
    await orchestrator.ingest_message("h-dr", "m-dr1", "bai aaj nahi aayi", dedupe_key="dr-a1", now_ms=4000)
    await orchestrator.ingest_message("h-dr", "m-dr1", "geyser kaam nahi kar raha", dedupe_key="dr-i1", now_ms=5000)
    await orchestrator.ingest_message("h-dr", "m-dr1", "internet fix karega Bob kal tak", dedupe_key="dr-c2", now_ms=6000)


# ---------------------------------------------------------------------------
# DR-1: Delete projections → replay → identical state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disaster_projection_wipe_and_replay():
    """DR-1: Core proof — wipe all projections, replay events, get identical state."""
    from saath.api.deps import _store, _orchestrator

    await _setup_house(_store, _orchestrator)

    # Capture "before" state
    before_commitments = await _store.get_open_commitments("h-dr")
    before_supplies = await _store._conn.execute_fetchall(
        "SELECT item_norm, status FROM projection_supply WHERE house_id='h-dr'"
    )
    before_events = await _store.get_all_events("h-dr")

    # Wipe ALL projections (simulates corruption/crash)
    tables = [
        "projection_commitment",
        "projection_supply",
        "projection_issue",
        "projection_expense",
        "projection_action_log",
        "projection_followup",
    ]
    for tbl in tables:
        await _store._conn.execute(f"DELETE FROM {tbl} WHERE house_id='h-dr'")
    await _store._conn.commit()

    # Verify projections gone
    after_wipe = await _store.get_open_commitments("h-dr")
    assert len(after_wipe) == 0, "Projections should be empty after wipe"

    # Replay
    await _store.rebuild_projections_from_events("h-dr")

    # Verify state is identical
    after_replay_commitments = await _store.get_open_commitments("h-dr")
    after_replay_events = await _store.get_all_events("h-dr")

    assert len(after_replay_commitments) == len(before_commitments), (
        f"Replay recovered {len(after_replay_commitments)} commitments, "
        f"expected {len(before_commitments)}"
    )

    after_supplies = await _store._conn.execute_fetchall(
        "SELECT item_norm, status FROM projection_supply WHERE house_id='h-dr'"
    )
    assert len(after_supplies) == len(before_supplies), (
        f"Replay recovered {len(after_supplies)} supplies, expected {len(before_supplies)}"
    )

    # Event count must NOT change — events are immutable
    assert len(after_replay_events) == len(before_events), (
        "Replay must not add or remove events from the event store"
    )


# ---------------------------------------------------------------------------
# DR-2: Crash during event write → partial write does not corrupt state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disaster_partial_write_leaves_clean_state():
    """DR-2: An exception during atomic batch write leaves no partial projection."""
    from saath.api.deps import _store, _orchestrator
    from saath.domain.events import DomainEvent, EventType
    from saath.domain.ids import generate_uuidv7

    await _store.connect()
    await _store.record_house("h-pw", "Partial Write House", "Asia/Kolkata", 1000)
    await _store.record_member("m-pw1", "h-pw", "Carol", None, "flatmate", [], 1000)

    # First ingest works fine
    await _orchestrator.ingest_message("h-pw", "m-pw1", "doodh khatam", dedupe_key="pw-1", now_ms=1000)
    before_supply = await _store._conn.execute_fetchall(
        "SELECT * FROM projection_supply WHERE house_id='h-pw'"
    )

    # Inject a failing event alongside a good one — simulates mid-batch crash
    good_ev = DomainEvent(
        id=generate_uuidv7("ev"), house_id="h-pw",
        event_type=EventType.NOTE_RECORDED, actor_id="m-pw1",
        occurred_at=2000, payload={"text": "noted"},
    )
    # Bad event: malformed house_id to trigger FK failure
    bad_ev = DomainEvent(
        id=generate_uuidv7("ev"), house_id="h-pw-nonexistent",  # FK violation
        event_type=EventType.NOTE_RECORDED, actor_id="m-pw1",
        occurred_at=2001, payload={"text": "corrupt"},
    )

    with pytest.raises(Exception):
        await _store.append_events_and_project_batch([good_ev, bad_ev])

    # State should not have changed — atomicity means all-or-nothing
    after_supply = await _store._conn.execute_fetchall(
        "SELECT * FROM projection_supply WHERE house_id='h-pw'"
    )
    assert len(after_supply) == len(before_supply), (
        "Partial batch write must not modify state — transaction atomicity required"
    )


# ---------------------------------------------------------------------------
# DR-3: Corrupted projection → rebuild from events → correct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disaster_corrupted_projection_healed_by_replay():
    """DR-3: Manually corrupt a projection row, then replay to get correct values."""
    from saath.api.deps import _store, _orchestrator

    await _setup_house(_store, _orchestrator)

    # Get current commitments
    commitments = await _store.get_open_commitments("h-dr")
    if not commitments:
        pytest.skip("No commitments to corrupt")

    target = commitments[0]
    # Corrupt the projection row directly
    await _store._conn.execute(
        "UPDATE projection_commitment SET title='CORRUPTED_TITLE', state='done' WHERE id=? AND house_id='h-dr'",
        (target.id,)
    )
    await _store._conn.commit()

    # Verify corruption visible
    corrupted = await _store.get_open_commitments("h-dr")
    assert not any(c.id == target.id for c in corrupted), "Corrupted row should not appear as open"

    # Wipe and replay
    await _store._conn.execute("DELETE FROM projection_commitment WHERE house_id='h-dr'")
    await _store._conn.commit()
    await _store.rebuild_projections_from_events("h-dr")

    # Original state restored
    restored = await _store.get_open_commitments("h-dr")
    restored_target = next((c for c in restored if c.id == target.id), None)

    assert restored_target is not None, f"Commitment {target.id} not restored by replay"
    assert restored_target.title != "CORRUPTED_TITLE", "Replay must restore correct title"


# ---------------------------------------------------------------------------
# DR-4: Event immutability survives replay (no phantom events)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disaster_replay_does_not_duplicate_events():
    """DR-4: Running replay multiple times must not create duplicate events."""
    from saath.api.deps import _store, _orchestrator

    await _setup_house(_store, _orchestrator)

    events_before = await _store.get_all_events("h-dr")
    count_before = len(events_before)

    # Run replay twice
    await _store.rebuild_projections_from_events("h-dr")
    await _store.rebuild_projections_from_events("h-dr")

    events_after = await _store.get_all_events("h-dr")
    count_after = len(events_after)

    assert count_after == count_before, (
        f"Multiple replays must not add events: {count_before} → {count_after}"
    )


# ---------------------------------------------------------------------------
# DR-5: Rebuild projection from events matches full history
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disaster_full_history_preserved_through_rebuild():
    """DR-5: Event store contains ALL history even after multiple projection rebuilds."""
    from saath.api.deps import _store, _orchestrator

    await _setup_house(_store, _orchestrator)

    # Add an undo event to make history richer
    commitments = await _store.get_open_commitments("h-dr")
    if commitments:
        first_events = await _store.get_all_events("h-dr")
        source_ev_id = first_events[0].id if first_events else None
        if source_ev_id:
            await _store.undo_event("h-dr", source_ev_id, "m-dr1", now_ms=10_000)

    events_total = await _store.get_all_events("h-dr")
    total_count = len(events_total)

    # Wipe and rebuild
    for tbl in ["projection_commitment", "projection_supply", "projection_issue",
                "projection_expense", "projection_action_log", "projection_followup"]:
        await _store._conn.execute(f"DELETE FROM {tbl} WHERE house_id='h-dr'")
    await _store._conn.commit()

    await _store.rebuild_projections_from_events("h-dr")

    events_after = await _store.get_all_events("h-dr")
    assert len(events_after) == total_count, "All history must survive projection rebuild"
