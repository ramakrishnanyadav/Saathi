"""Security tests for Multi-Tenant House Scoping and Cross-House Isolation."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from saath.api.deps import get_store, reset_app_state
from saath.api.main import app
from saath.domain.events import CommitmentState, DomainEvent, EventType


@pytest.fixture(autouse=True)
async def isolated_env():
    reset_app_state(":memory:")
    store = await get_store()
    # House 1
    await store.record_house("h-alpha", "Alpha House", "Asia/Kolkata", 1000)
    await store.record_member("m-alpha-1", "h-alpha", "Alice", None, "flatmate", [], 1000)
    # House 2
    await store.record_house("h-beta", "Beta House", "Asia/Kolkata", 1000)
    await store.record_member("m-beta-1", "h-beta", "Bob", None, "flatmate", [], 1000)

    # Seed commitment in House Alpha
    ev = DomainEvent(
        id="ev-c-alpha",
        house_id="h-alpha",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-alpha-1",
        occurred_at=1000,
        payload={
            "commitment_id": "c-alpha-secret",
            "title": "Fix Alpha geyser",
            "responsible_party": "Landlord",
            "promise_made_by": "Landlord",
            "tracked_by": "m-alpha-1",
            "due_at": 2000,
            "status": CommitmentState.WAITING.value,
        },
    )
    await store.append_event_and_project(ev)
    yield
    reset_app_state(":memory:")


@pytest.mark.asyncio
async def test_cross_house_commitment_isolation():
    """House Beta MUST NOT be able to view or transition House Alpha commitments."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. House Alpha can see its commitment
        res_alpha = await client.get("/api/v1/attention", headers={"X-House-Id": "h-alpha"})
        assert res_alpha.status_code == 200
        alpha_items = res_alpha.json()["overdue"] + res_alpha.json()["waiting"]
        titles = [item["title"] for item in alpha_items]
        assert "Fix Alpha geyser" in titles

        # 2. House Beta cannot see House Alpha's commitment in attention
        res_beta = await client.get("/api/v1/attention", headers={"X-House-Id": "h-beta"})
        assert res_beta.status_code == 200
        beta_items = res_beta.json()["overdue"] + res_beta.json()["waiting"]
        assert len(beta_items) == 0

        # 3. House Beta attempting to mark done House Alpha's commitment -> 404
        res_cross_done = await client.post(
            "/api/v1/commitments/c-alpha-secret/done",
            headers={"X-House-Id": "h-beta"},
            json={"actor_id": "m-beta-1"},
        )
        assert res_cross_done.status_code == 404
        assert "not found" in res_cross_done.json()["detail"].lower()


@pytest.mark.asyncio
async def test_missing_house_header_rejected():
    """Requests without house scoping header must return 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty X-House-Id header
        res = await client.get("/api/v1/attention", headers={"X-House-Id": ""})
        assert res.status_code == 400
        assert "X-House-Id" in res.json()["detail"]


@pytest.mark.asyncio
async def test_cross_house_actor_rejected():
    """Member from House Beta must be rejected (403) when attempting actions in House Alpha."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/commitments/c-alpha-secret/done",
            headers={"X-House-Id": "h-alpha", "X-Member-Id": "m-beta-1"},
            json={"actor_id": "m-beta-1"},
        )
        assert res.status_code == 403
        assert "does not belong" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_confirm_expense_validation_and_idempotency():
    """Expense confirmation must enforce member house boundaries, share summation, and double-click idempotency."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Payer from House Beta in House Alpha -> 403
        res_bad_payer = await client.post(
            "/api/v1/events/confirm",
            headers={"X-House-Id": "h-alpha", "X-Member-Id": "m-alpha-1"},
            json={
                "expense_id": "exp-101",
                "amount_paise": 30000,
                "paid_by": "m-beta-1",  # Invalid cross-house member
                "shares": {"m-alpha-1": 30000},
                "participants": ["m-alpha-1"],
            },
        )
        assert res_bad_payer.status_code == 403

        # 2. Participant shares do not sum to total amount_paise -> 422
        res_bad_sum = await client.post(
            "/api/v1/events/confirm",
            headers={"X-House-Id": "h-alpha", "X-Member-Id": "m-alpha-1"},
            json={
                "expense_id": "exp-101",
                "amount_paise": 30000,
                "paid_by": "m-alpha-1",
                "shares": {"m-alpha-1": 25000},  # 25000 != 30000
                "participants": ["m-alpha-1"],
            },
        )
        assert res_bad_sum.status_code == 422

        # 3. Valid confirmation -> 200
        res_valid = await client.post(
            "/api/v1/events/confirm",
            headers={"X-House-Id": "h-alpha", "X-Member-Id": "m-alpha-1"},
            json={
                "expense_id": "exp-101",
                "amount_paise": 30000,
                "paid_by": "m-alpha-1",
                "shares": {"m-alpha-1": 30000},
                "participants": ["m-alpha-1"],
                "category": "groceries",
                "description": "Vegetables",
            },
        )
        assert res_valid.status_code == 200
        data = res_valid.json()
        assert data["status"] == "confirmed"
        assert data["already_confirmed"] is False

        # 4. Immediate duplicate confirmation (simulating rapid double-click) -> idempotent 200 with already_confirmed=True
        res_duplicate = await client.post(
            "/api/v1/events/confirm",
            headers={"X-House-Id": "h-alpha", "X-Member-Id": "m-alpha-1"},
            json={
                "expense_id": "exp-101",
                "amount_paise": 30000,
                "paid_by": "m-alpha-1",
                "shares": {"m-alpha-1": 30000},
                "participants": ["m-alpha-1"],
            },
        )
        assert res_duplicate.status_code == 200
        assert res_duplicate.json()["already_confirmed"] is True


@pytest.mark.asyncio
async def test_same_entity_id_in_different_houses():
    """Identical commitment IDs in separate houses must remain isolated and never overwrite each other."""
    store = await get_store()

    # Commitments with the same ID in both Alpha and Beta
    ev_alpha = DomainEvent(
        id="ev-alpha-same",
        house_id="h-alpha",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-alpha-1",
        occurred_at=1000,
        payload={
            "commitment_id": "shared-id-123",
            "title": "Alpha Tap Repair",
            "responsible_party": "Landlord",
            "promise_made_by": "Landlord",
            "tracked_by": "m-alpha-1",
            "due_at": 5000,
            "status": CommitmentState.WAITING.value,
        },
    )
    await store.append_event_and_project(ev_alpha)

    ev_beta = DomainEvent(
        id="ev-beta-same",
        house_id="h-beta",
        event_type=EventType.COMMITMENT_CREATED,
        actor_id="m-beta-1",
        occurred_at=1100,
        payload={
            "commitment_id": "shared-id-123",
            "title": "Beta Gas Cylinder",
            "responsible_party": "Agency",
            "promise_made_by": "Agency",
            "tracked_by": "m-beta-1",
            "due_at": 6000,
            "status": CommitmentState.WAITING.value,
        },
    )
    await store.append_event_and_project(ev_beta)

    # Verify both exist independently with their own titles
    c_alpha = await store.get_commitment_by_id("shared-id-123", house_id="h-alpha")
    c_beta = await store.get_commitment_by_id("shared-id-123", house_id="h-beta")

    assert c_alpha is not None
    assert c_alpha.title == "Alpha Tap Repair"

    assert c_beta is not None
    assert c_beta.title == "Beta Gas Cylinder"

