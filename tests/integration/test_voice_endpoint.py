"""Integration tests for Voice/Audio Ingestion Endpoint with security checks."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from saath.api.deps import reset_app_state
from saath.api.main import app


@pytest.fixture(autouse=True)
async def isolated_env():
    """Ensure in-memory clean database for voice endpoint tests."""
    reset_app_state(":memory:")
    from saath.api.deps import get_store
    store = await get_store()
    await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", 1000)
    await store.record_member("m-1", "h-demo", "You", None, "flatmate", ["me"], 1000)
    yield
    reset_app_state(":memory:")


@pytest.mark.asyncio
async def test_voice_upload_and_ingestion(monkeypatch):
    monkeypatch.setenv("SAATH_SIMULATE_STT", "1")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Valid WAV audio upload with simulated STT
        dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        files = {"file": ("recording.wav", dummy_wav, "audio/wav")}
        data = {"author_id": "m-1"}

        res = await client.post(
            "/api/v1/messages/voice",
            headers={"X-House-Id": "h-demo"},
            files=files,
            data=data,
        )

        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert "transcribed_text" in body
        assert any(ev["type"] == "commitment_created" for ev in body["applied_events"])
        assert any(ev["type"] == "issue_reported" for ev in body["applied_events"])


@pytest.mark.asyncio
async def test_voice_upload_unrecognized_speech_returns_422(monkeypatch):
    monkeypatch.delenv("SAATH_SIMULATE_STT", raising=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        files = {"file": ("unintelligible.wav", dummy_wav, "audio/wav")}

        res = await client.post(
            "/api/v1/messages/voice",
            headers={"X-House-Id": "h-demo"},
            files=files,
            data={"author_id": "m-1"},
        )

        assert res.status_code == 422
        assert "Speech Unrecognized" in res.json()["title"]


@pytest.mark.asyncio
async def test_voice_upload_size_limit_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Oversized audio (> 5 MB)
        oversized_data = b"0" * (5 * 1024 * 1024 + 10)
        files = {"file": ("big.wav", oversized_data, "audio/wav")}

        res = await client.post(
            "/api/v1/messages/voice",
            headers={"X-House-Id": "h-demo"},
            files=files,
            data={"author_id": "m-1"},
        )

        assert res.status_code == 413
        assert "exceeds maximum allowed limit of 5 MB" in res.json()["detail"]


@pytest.mark.asyncio
async def test_voice_upload_unsupported_mime_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("malicious.exe", b"MZ...", "application/x-msdownload")}

        res = await client.post(
            "/api/v1/messages/voice",
            headers={"X-House-Id": "h-demo"},
            files=files,
            data={"author_id": "m-1"},
        )

        assert res.status_code == 415
        assert "not supported" in res.json()["detail"]
