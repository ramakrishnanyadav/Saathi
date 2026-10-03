"""Tests for deterministic event replay equivalence."""

import pytest
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.domain.commitments import CommitmentState
from saath.domain.events import DomainEvent, EventType


@pytest.mark.asyncio
async def test_replay_equivalence():
    """
    Events -> live projections vs. Events -> clear -> replay -> rebuilt projections
    must yield 100% equivalent state.
    """
    store = SQLiteEventStore(":memory:")
    await store.record_house("h-1", "Test Flat", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-1", "Alice", "+919876543210", "flatmate", [], 1000)
    await store.record_member("m-2", "h-1", "Bob", "+919876543211", "flatmate", [], 1000)

    # 1. Create a series of events
    # Event 1: Issue
    ev1 = DomainEvent(
        id="ev-1",
        house_id="h-1",
        event_type=EventType.ISSUE_REPORTED,
        actor_id="m-1",
        occurred_at=1000,
        payload={"issue_id": "iss-1", "title": "Kitchen sink leak"},
    )
    # Event 2: Commitment
    ev2 = DomainEvent(
        id="ev-2",
        house_id="h-1",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-1",
        occurred_at=2000,
        payload={
            "commitment_id": "c-1",
            "title": "Landlord plumber promise",
            "promise_made_by": "Landlord",
            "responsible_party": "Landlord",
            "tracked_by": "m-1",
            "due_at": 5000,
            "issue_id": "iss-1",
        },
    )
    # Event 3: Reschedule
    ev3 = DomainEvent(
        id="ev-3",
        house_id="h-1",
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id="m-1",
        occurred_at=6000,
        payload={
            "commitment_id": "c-1",
            "new_state": "rescheduled",
            "new_due_at": 10000,
        },
    )
    # Event 4: Expense
    ev4 = DomainEvent(
        id="ev-4",
        house_id="h-1",
        event_type=EventType.EXPENSE_CREATED,
        actor_id="m-2",
        occurred_at=7000,
        payload={
            "expense_id": "exp-1",
            "title": "Grocery run",
            "amount_paise": 50000,
            "paid_by": "m-2",
            "shares": {"m-1": 25000, "m-2": 25000},
            "is_confirmed": False,
        },
    )

    for ev in [ev1, ev2, ev3, ev4]:
        await store.append_event_and_project(ev)

    # Capture live state
    live_commitments = await store.get_open_commitments("h-1")
    assert len(live_commitments) == 1
    assert live_commitments[0].due_at == 10000
    assert live_commitments[0].state == CommitmentState.WAITING

    # 2. Rebuild projections from events
    await store.rebuild_projections_from_events("h-1")

    # Re-capture rebuilt state
    rebuilt_commitments = await store.get_open_commitments("h-1")
    assert len(rebuilt_commitments) == 1
    assert rebuilt_commitments[0].id == live_commitments[0].id
    assert rebuilt_commitments[0].due_at == live_commitments[0].due_at
    assert rebuilt_commitments[0].state == live_commitments[0].state
    assert rebuilt_commitments[0].title == live_commitments[0].title

    await store.close()
