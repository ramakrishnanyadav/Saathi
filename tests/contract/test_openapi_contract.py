"""
SAATH API Contract Testing
Validates OpenAPI 3.0 schema and endpoint contract invariants.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from saath.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_openapi_schema_validity(client: TestClient):
    """OpenAPI schema generation must succeed and contain expected endpoints."""
    r = client.get("/openapi.json")
    assert r.status_code == 200, f"OpenAPI schema fetch failed with status {r.status_code}"

    schema = r.json()
    assert schema.get("openapi", "").startswith("3.")
    assert schema["info"]["title"] == "SAATH API"

    paths = schema.get("paths", {})

    # Required endpoints contract checklist
    required_endpoints = [
        "/healthz",
        "/readyz",
        "/metrics",
        "/api/v1/house/members",
        "/api/v1/messages",
        "/api/v1/messages/voice",
        "/api/v1/attention",
        "/api/v1/commitments/{commitment_id}",
        "/api/v1/commitments/{commitment_id}/done",
        "/api/v1/commitments/{commitment_id}/snooze",
        "/api/v1/commitments/{commitment_id}/reschedule",
        "/api/v1/commitments/{commitment_id}/followup",
        "/api/v1/followups/{commitment_id}/opened",
        "/api/v1/followups/{commitment_id}/sent",
        "/api/v1/events/confirm",
        "/api/v1/expenses/confirm",
        "/api/v1/events/{event_id}/undo",
        "/api/v1/reflection",
        "/api/v1/history",
        "/api/v1/sync/outbox",
        "/api/v1/demo/clock/advance",
        "/api/v1/demo/seed",
    ]

    for ep in required_endpoints:
        assert ep in paths, f"API contract missing required endpoint: '{ep}'"


def test_request_response_headers_contract(client: TestClient):
    """Endpoints must return observability response headers."""
    r = client.get("/healthz")
    assert r.status_code == 200
    assert "X-SAATH-Stage" in r.headers
    assert "X-SAATH-Duration-Ms" in r.headers
