"""Integration tests for FastAPI endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from saath.api.deps import reset_app_state
from saath.api.main import app


@pytest.mark.asyncio
async def test_api_health_and_core_workflow():
    reset_app_state(":memory:")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res_h = await client.get("/healthz")
        assert res_h.status_code == 200
        assert res_h.json()["status"] == "ok"

        # Seed flatmates via seed endpoint
        res_seed = await client.post("/api/v1/demo/seed", headers={"X-House-Id": "h-demo"})
        assert res_seed.status_code == 200

        # 2. Ingest message
        res_msg = await client.post(
            "/api/v1/messages",
            headers={"X-House-Id": "h-demo"},
            json={
                "text": "Bhai tap leak ho raha hai, landlord bola kal plumber bhejega",
                "author_id": "m-1",
            },
        )
        assert res_msg.status_code == 200
        data_msg = res_msg.json()
        assert data_msg["success"] is True
        assert len(data_msg["applied_events"]) >= 1

        # 3. Check attention (initially waiting)
        res_att = await client.get("/api/v1/attention", headers={"X-House-Id": "h-demo"})
        assert res_att.status_code == 200
        data_att = res_att.json()
        assert len(data_att["waiting"]) >= 1
        cid = data_att["waiting"][0]["id"]

        # 4. Advance demo clock by 48 hours -> Should become overdue!
        res_adv = await client.post(
            "/api/v1/demo/clock/advance",
            json={"delta_hours": 48.0},
        )
        assert res_adv.status_code == 200

        # 5. Check attention again -> Now in overdue!
        res_att2 = await client.get("/api/v1/attention", headers={"X-House-Id": "h-demo"})
        data_att2 = res_att2.json()
        assert len(data_att2["overdue"]) >= 1
        assert any(item["id"] == cid for item in data_att2["overdue"])
        overdue_item = next(item for item in data_att2["overdue"] if item["id"] == cid)
        assert overdue_item["is_overdue"] is True

        # 6. Generate follow-up draft
        res_draft = await client.post(
            f"/api/v1/commitments/{cid}/followup",
            headers={"X-House-Id": "h-demo"},
            params={"phone": "+919876543210"},
        )
        assert res_draft.status_code == 200
        data_draft = res_draft.json()
        assert "Landlord" in data_draft["draft"]["draft_text"]
        assert "wa.me" in data_draft["draft"]["whatsapp_url"]

        # 7. Outbox sync
        res_sync = await client.post(
            "/api/v1/sync/outbox",
            headers={"X-House-Id": "h-demo"},
            json={
                "items": [
                    {"client_uuid": "sync-u-1", "text": "doodh khatam hai", "author_id": "m-1"},
                    {"client_uuid": "sync-u-2", "text": "maine plumber ko 2 baar call kiya", "author_id": "m-1"},
                ]
            },
        )
        assert res_sync.status_code == 200
        assert res_sync.json()["synced_count"] == 2
