"""Integration tests for Partner Tech endpoints (ElevenLabs Voice Check-in & Sentry Tracing)."""

import pytest
from fastapi.testclient import TestClient
from saath.api import deps
from saath.api.main import app

H = {"X-House-Id": "h-demo", "X-Member-Id": "m-1"}


@pytest.fixture()
def client():
    deps.reset_app_state(":memory:")
    with TestClient(app) as c:
        yield c


def test_elevenlabs_voice_followup_endpoint(client):
    # Ingest message to create commitment
    res_msg = client.post(
        "/api/v1/messages",
        headers=H,
        json={"text": "Bhai tap leak ho raha hai, landlord bola kal plumber bhejega", "author_id": "m-1"},
    )
    assert res_msg.status_code == 200

    # Query attention to get commitment id
    res_att = client.get("/api/v1/attention", headers=H)
    assert res_att.status_code == 200
    waiting = res_att.json().get("waiting", [])
    assert len(waiting) >= 1
    cid = waiting[0]["id"]

    # Request ElevenLabs voice check-in
    res_voice = client.post(f"/api/v1/commitments/{cid}/voice_followup", headers=H)
    assert res_voice.status_code == 200
    data = res_voice.json()
    assert data["success"] is True
    assert data["commitment_id"] == cid
    assert "voice" in data
    assert data["voice"]["audio_url"].startswith("data:audio/mpeg;base64,")


def test_sentry_tracing_headers(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert "X-SAATH-Stage" in res.headers
    assert "X-SAATH-Duration-Ms" in res.headers


def test_sentry_debug_route(client):
    with pytest.raises(ZeroDivisionError):
        client.get("/sentry-debug")
