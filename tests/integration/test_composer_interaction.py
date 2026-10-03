"""Comprehensive Integration Tests for Composer / Input Interaction Journey (Reqs A - N)."""

import pytest
from httpx import ASGITransport, AsyncClient
from saath.api.deps import reset_app_state
from saath.api.main import app


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_app_state(":memory:")


@pytest.mark.asyncio
async def test_composer_journey_empty_submit_validation():
    """B, F. Empty or whitespace submit returns HTTP 422 validation error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={"text": "   ", "author_id": "m-1"},
        )
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_composer_journey_missing_house_header_400():
    """D. Missing house header returns HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/messages",
            json={"text": "Rahul will pay bill tomorrow", "author_id": "m-1"},
        )
        assert res.status_code == 400
        data = res.json()
        assert "X-House-Id" in data["detail"]


@pytest.mark.asyncio
async def test_composer_journey_successful_commitment_submit():
    """C, N. Successful submit extracts commitment (WHAT, WHO, WHEN)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={
                "text": "Landlord promised to fix bathroom leak tomorrow",
                "author_id": "m-1",
                "dedupe_key": "dedupe-comp-1",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["applied_events"]) >= 1
        
        # Verify commitment state created and reflected in attention
        res_att = await client.get("/api/v1/attention", headers={"X-House-Id": "h-demo"})
        assert res_att.status_code == 200
        data_att = res_att.json()
        assert len(data_att["waiting"]) >= 1


@pytest.mark.asyncio
async def test_composer_journey_money_confirmation_flow():
    """M. Money detection extracts financial event or pending confirmation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={
                "text": "I paid 1500 for electricity bill",
                "author_id": "m-1",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["pending_confirmations"]) >= 1 or len(data["applied_events"]) >= 1


@pytest.mark.asyncio
async def test_composer_journey_duplicate_submission_deduplication():
    """K. Duplicate submission with same dedupe_key produces exactly one result."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dedupe = "unique-key-999"
        res1 = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={"text": "Amit will buy groceries tomorrow", "author_id": "m-1", "dedupe_key": dedupe},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["is_duplicate"] is False

        # Duplicate submit
        res2 = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={"text": "Amit will buy groceries tomorrow", "author_id": "m-1", "dedupe_key": dedupe},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["is_duplicate"] is True


@pytest.mark.asyncio
async def test_composer_journey_ambiguity_resolution():
    """L. Ambiguity surfaces resolution structure for user clarification."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create initial commitment
        await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={"text": "Rahul will pay electricity bill Friday", "author_id": "m-1"},
        )

        # Ambiguous reply referring to vague statement
        res = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={"text": "He did it yesterday", "author_id": "m-1"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "reply_resolution" in data


@pytest.mark.asyncio
async def test_composer_journey_offline_outbox_queue():
    """H, I, J. Outbox endpoint processes queued offline items cleanly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sync/outbox",
            headers={"X-House-Id": "h-demo"},
            json={
                "items": [
                    {"client_uuid": "offline-item-1", "text": "Bought salt and milk", "author_id": "m-1"},
                ]
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["synced_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] in ("applied", "synced")
