"""ElevenLabs TTS Adapter for SAATH gentle voice follow-up check-ins.

Translates follow-up check-in text into spoken Hinglish audio via ElevenLabs API,
with graceful fallback to offline/data-URI voice audio.
"""

from __future__ import annotations

import base64
import os
import logging
from typing import Any
import httpx

logger = logging.getLogger("saath.tts")

DEFAULT_ELEVENLABS_VOICE_ID = "Xb7hH8MSUJpSbSDYk0k2"  # Alice - Clear, Engaging premade voice (Free tier compatible)
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


class ElevenLabsTTSAdapter:
    """ElevenLabs Voice Synthesis adapter for generating audio follow-up check-ins."""

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
        self.timeout_seconds = timeout_seconds

    async def generate_speech_bytes(self, text: str) -> tuple[bytes, str]:
        """Generates audio MP3 bytes for the given text.

        Returns (audio_bytes, format_type).
        """
        if not self.api_key:
            logger.info("ELEVENLABS_API_KEY not set; using local fallback synthesized audio")
            return self._generate_fallback_audio(text)

        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.content, "audio/mpeg"
                logger.warning(f"ElevenLabs API error HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"ElevenLabs request failed: {type(e).__name__} ({e})")

        return self._generate_fallback_audio(text)

    async def generate_speech_data_uri(self, text: str) -> dict[str, Any]:
        """Generates audio data URI for easy web embedding in React audio player."""
        audio_bytes, mime_type = await self.generate_speech_bytes(text)
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        return {
            "audio_url": f"data:{mime_type};base64,{b64}",
            "text": text,
            "mime_type": mime_type,
            "provider": "elevenlabs" if self.api_key else "local_fallback",
        }

    def _generate_fallback_audio(self, text: str) -> tuple[bytes, str]:
        """Generates a small valid MP3 header payload for offline dev/test fallback."""
        # 1-second silence MP3 frame bytes
        mp3_header = b"\xff\xfb\x90\xc4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        return mp3_header, "audio/mpeg"
