"""Integration tests for Event Undo, Malicious AI Output Rejection, and Partial Outbox Sync."""

import pytest
from httpx import ASGITransport, AsyncClient
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.api.deps import get_store, reset_app_state
from saath.api.main import app
from saath.application.validator import ExtractionValidationError, validate_extracted_event
from saath.domain.commitments import CommitmentState
from saath.domain.events import DomainEvent, EventType
from saath.domain.ids import generate_uuidv7


@pytest.fixture(autouse=True)
async def isolated_env():
    reset_app_state(":memory:")
    store = await get_store()
    await store.record_house("h-demo", "Demo House", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-demo", "You", None, "flatmate", [], 1000)
    await store.record_member("m-2", "h-demo", "Rahul", None, "flatmate", [], 1000)
    yield
    reset_app_state(":memory:")


@pytest.mark.asyncio
async def test_event_undo_and_replay_equivalence():
    """Undoing an event must restore previous state and preserve replay equivalence."""
    store = await get_store()
    transport = ASGITransport(app=app)
    cid = generate_uuidv7("comm")

    # 1. Create a commitment in waiting state
    ev_comm = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id="h-demo",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-1",
        occurred_at=1000,
        payload={
            "commitment_id": cid,
            "title": "Fix water purifier",
            "responsible_party": "Technician",
            "promise_made_by": "Technician",
            "tracked_by": "m-1",
            "due_at": 5000,
            "status": CommitmentState.WAITING.value,
        },
    )
    await store.append_event_and_project(ev_comm)

    comm = await store.get_commitment_by_id(cid, house_id="h-demo")
    assert comm is not None
    assert comm.state == CommitmentState.WAITING

    # 2. Mark commitment done via API
    ev_done_id = generate_uuidv7("ev")
    ev_done = DomainEvent(
        id=ev_done_id,
        house_id="h-demo",
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id="m-1",
        occurred_at=2000,
        payload={"commitment_id": cid, "new_state": "done", "actor_id": "m-1"},
    )
    await store.append_event_and_project(ev_done)

    comm_done = await store.get_commitment_by_id(cid, house_id="h-demo")
    assert comm_done.state == CommitmentState.DONE

    # 3. Call Undo on the done event
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/events/{ev_done_id}/undo",
            headers={"X-House-Id": "h-demo", "X-Member-Id": "m-1"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "superseded"

        # 4. State should revert to WAITING
        comm_restored = await store.get_commitment_by_id(cid, house_id="h-demo")
        assert comm_restored.state == CommitmentState.WAITING

        # 5. Replay must yield the exact same WAITING state
        await store.rebuild_projections_from_events(house_id="h-demo")
        comm_replayed = await store.get_commitment_by_id(cid, house_id="h-demo")
        assert comm_replayed.state == CommitmentState.WAITING

        # 6. Undoing again must fail
        res_repeat = await client.post(
            f"/api/v1/events/{ev_done_id}/undo",
            headers={"X-House-Id": "h-demo", "X-Member-Id": "m-1"},
        )
        assert res_repeat.status_code == 400


def test_malicious_ai_output_strictly_rejected():
    """AI outputs with forbidden extra fields, unknown types, or invalid members must raise ExtractionValidationError."""
    valid_members = ["m-1", "m-2"]

    # 1. Unknown event type -> Rejected
    with pytest.raises(ExtractionValidationError, match="Invalid event_type"):
        validate_extracted_event("admin_grant_root_access", {"foo": "bar"}, valid_members)

    # 2. Unexpected injected fields -> Rejected by extra='forbid'
    with pytest.raises(ExtractionValidationError):
        validate_extracted_event(
            "commitment_created",
            {
                "title": "Repair geyser",
                "responsible_party": "Landlord",
                "injected_command": "DROP TABLE member;",
            },
            valid_members,
        )

    # 3. Non-existent / injected member ID -> Rejected
    with pytest.raises(ExtractionValidationError, match="not a registered house member"):
        validate_extracted_event(
            "action_taken",
            {
                "label": "Paid bill",
                "kind": "coordination",
                "member_id": "m-999-attacker",
            },
            valid_members,
        )


@pytest.mark.asyncio
async def test_partial_outbox_sync_per_item_results():
    """Outbox sync must return granular per-item statuses and isolate failures."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit batch: 1 normal item, 1 duplicate item
        uuid1 = generate_uuidv7("sync")
        batch = {
            "items": [
                {
                    "client_uuid": uuid1,
                    "text": "Doodh khatam hai",
                    "author_id": "m-1",
                    "occurred_at": 1000,
                },
                {
                    "client_uuid": uuid1,  # Duplicate in same batch
                    "text": "Doodh khatam hai",
                    "author_id": "m-1",
                    "occurred_at": 1000,
                },
            ]
        }
        res = await client.post(
            "/api/v1/sync/outbox",
            headers={"X-House-Id": "h-demo", "X-Member-Id": "m-1"},
            json=batch,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["synced_count"] == 1
        items = data["items"]
        assert len(items) == 2
        assert items[0]["status"] == "applied"
        assert items[1]["status"] == "duplicate"
