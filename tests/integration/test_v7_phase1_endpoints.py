"""Integration tests for SAATH v7 Phase 1 endpoints (expenses, clock, reply, cancel)."""

import pytest
from fastapi.testclient import TestClient
from saath.api.main import app

client = TestClient(app)


def test_get_clock_endpoint():
    res = client.get("/api/v1/clock")
    assert res.status_code == 200
    data = res.json()
    assert "now_ms" in data
    assert "simulated" in data
    assert isinstance(data["now_ms"], int)


def test_expenses_endpoint():
    headers = {"X-House-Id": "h-demo", "X-Member-Id": "m-1"}
    res = client.get("/api/v1/expenses", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "expenses" in data
    assert isinstance(data["expenses"], list)


def test_commitment_reply_and_cancel_endpoints():
    headers = {"X-House-Id": "h-demo", "X-Member-Id": "m-1"}

    # First seed demo data so we have a commitment
    seed_res = client.post("/api/v1/demo/seed", headers=headers)
    assert seed_res.status_code == 200

    # Get attention items to find commitment id
    att_res = client.get("/api/v1/attention", headers=headers)
    assert att_res.status_code == 200
    att_data = att_res.json()
    commitments = att_data.get("waiting", []) + att_data.get("overdue", [])
    assert len(commitments) > 0
    cid = commitments[0]["id"]

    # Reply rescheduled
    reply_res = client.post(
        f"/api/v1/commitments/{cid}/reply",
        json={"intent": "rescheduled"},
        headers=headers,
    )
    assert reply_res.status_code == 200
    assert reply_res.json()["state"] == "rescheduled"

    # Cancel commitment
    cancel_res = client.post(
        f"/api/v1/commitments/{cid}/cancel",
        json={},
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["state"] == "cancelled"
