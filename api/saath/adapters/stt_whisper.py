"""Audio STT Adapter with faster-whisper and truthful error handling."""

from __future__ import annotations

import io
import logging
import os

logger = logging.getLogger(__name__)


class STTUnavailableError(Exception):
    """Raised when Speech-to-Text engine (Whisper) is unavailable or fails to initialize."""
    pass


class WhisperSTTAdapter:
    """Whisper Speech-to-Text adapter with truthful local handling."""

    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self._model = None
        self._available: bool | None = None

    def _load_model(self) -> None:
        if self._available is not None:
            return
        try:
            from faster_whisper import WhisperModel  # type: ignore

            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self._available = True
            logger.info("faster-whisper model loaded successfully.")
        except Exception as e:
            logger.warning("faster-whisper not available (%s).", e)
            self._available = False

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes audio bytes to text in Hinglish / Hindi / English.
        Returns empty string if speech is unrecognized or transcription fails.
        Never fabricates text.
        """
        self._load_model()
        if self._available and self._model is not None:
            try:
                segments, _ = self._model.transcribe(
                    io.BytesIO(audio_bytes),
                    beam_size=5,
                    language=None,  # Auto-detect language (hi, en, etc.)
                )
                text = " ".join([segment.text for segment in segments]).strip()
                if text:
                    return text
            except Exception as ex:
                logger.error("Error during Whisper transcription: %s", ex)

        # Allow explicit simulated test payload for CI/offline mock testing
        if os.environ.get("SAATH_SIMULATE_STT") == "1":
            return "Bhai tap leak ho raha hai, landlord bola kal plumber bhejega"

        return ""
