"""Integration tests for SQLite event store, immutability triggers, and projections."""

import aiosqlite
import pytest
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.domain.commitments import CommitmentState
from saath.domain.events import CommitmentCreatedPayload, DomainEvent, EventType


@pytest.mark.asyncio
async def test_event_append_and_projection():
    store = SQLiteEventStore(":memory:")
    await store.record_house("h-1", "Test Flat", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-1", "Alice", "+919876543210", "flatmate", ["Ali"], 1000)

    # Append commitment event
    payload = CommitmentCreatedPayload(
        title="Fix tap",
        promise_made_by="Landlord",
        responsible_party="Landlord",
        tracked_by="m-1",
        due_at=2000,
    )
    event = DomainEvent(
        id="ev-1",
        house_id="h-1",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-1",
        occurred_at=1000,
        payload={
            "commitment_id": "c-1",
            "title": payload.title,
            "promise_made_by": payload.promise_made_by,
            "responsible_party": payload.responsible_party,
            "tracked_by": payload.tracked_by,
            "due_at": payload.due_at,
        },
    )

    await store.append_event_and_project(event)

    # Verify event stored
    events = await store.get_all_events("h-1")
    assert len(events) == 1
    assert events[0].id == "ev-1"

    # Verify projection created
    commitments = await store.get_open_commitments("h-1")
    assert len(commitments) == 1
    assert commitments[0].id == "c-1"
    assert commitments[0].title == "Fix tap"
    assert commitments[0].state == CommitmentState.WAITING

    await store.close()


@pytest.mark.asyncio
async def test_event_immutability_triggers():
    """Triggers MUST block UPDATE and DELETE on event table, raising ABORT."""
    store = SQLiteEventStore(":memory:")
    await store.record_house("h-1", "Test Flat", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-1", "Alice", "+919876543210", "flatmate", [], 1000)

    event = DomainEvent(
        id="ev-1",
        house_id="h-1",
        event_type=EventType.NOTE_RECORDED,
        actor_id="m-1",
        occurred_at=1000,
        payload={"text": "Initial note"},
    )
    await store.append_event_and_project(event)

    conn = await store.connect()

    # Attempt UPDATE on event -> must trigger RAISE(ABORT, 'events are immutable')
    with pytest.raises(aiosqlite.IntegrityError, match="events are immutable"):
        await conn.execute("UPDATE event SET status = 'tampered' WHERE id = 'ev-1'")

    # Attempt DELETE on event -> must trigger RAISE(ABORT, 'events are immutable')
    with pytest.raises(aiosqlite.IntegrityError, match="events are immutable"):
        await conn.execute("DELETE FROM event WHERE id = 'ev-1'")

    await store.close()
