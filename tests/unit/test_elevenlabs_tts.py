"""Unit tests for ElevenLabs Voice Synthesis (TTS) Adapter."""

import pytest
from saath.adapters.tts_elevenlabs import ElevenLabsTTSAdapter


@pytest.mark.asyncio
async def test_elevenlabs_fallback_data_uri():
    adapter = ElevenLabsTTSAdapter(api_key=None)
    res = await adapter.generate_speech_data_uri("Rahul bhai plumber update lagaya kya?")

    assert res["provider"] == "local_fallback"
    assert res["mime_type"] == "audio/mpeg"
    assert res["audio_url"].startswith("data:audio/mpeg;base64,")
    assert "Rahul" in res["text"]


@pytest.mark.asyncio
async def test_elevenlabs_speech_bytes():
    adapter = ElevenLabsTTSAdapter(api_key=None)
    audio_bytes, mime = await adapter.generate_speech_bytes("Test speech check-in")

    assert len(audio_bytes) > 0
    assert mime == "audio/mpeg"
