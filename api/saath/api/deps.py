"""FastAPI dependencies, authentication context, and singleton container for SAATH."""

from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Depends, Header
from saath.adapters.clock_sim import SimClock
from saath.adapters.llm_ollama import OllamaLLMProvider
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.adapters.stt_whisper import WhisperSTTAdapter
from saath.adapters.tts_elevenlabs import ElevenLabsTTSAdapter
from saath.api.errors import ProblemDetailException
from saath.application.orchestrator import SaathOrchestrator


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Authenticated household member context."""
    house_id: str
    member_id: str
    member_name: str
    role: str = "flatmate"


import time
from pathlib import Path

DB_PATH = os.environ.get("SAATH_DB_PATH", "data/saath.db")
if DB_PATH != ":memory:":
    db_dir = Path(DB_PATH).parent
    if str(db_dir) and not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)

_store = SQLiteEventStore(DB_PATH)
_clock = SimClock(initial_ms=int(time.time() * 1000))
_llm_timeout = float(os.environ.get("SAATH_LLM_TIMEOUT_S", os.environ.get("OLLAMA_TIMEOUT_SECONDS", "20.0")))
_llm = OllamaLLMProvider(
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
    model=os.environ.get("OLLAMA_MODEL", "gemma2:2b"),
    timeout_seconds=_llm_timeout,
)
_orchestrator = SaathOrchestrator(_store, _llm)
_stt = WhisperSTTAdapter()
_tts = ElevenLabsTTSAdapter()


def reset_app_state(db_path: str = ":memory:") -> None:
    """Helper to reset app state for isolated test execution."""
    global _store, _clock, _llm, _orchestrator, _stt, _tts
    _store = SQLiteEventStore(db_path)
    _clock = SimClock(initial_ms=int(time.time() * 1000))
    _llm = OllamaLLMProvider(timeout_seconds=0.1)
    _orchestrator = SaathOrchestrator(_store, _llm)
    _stt = WhisperSTTAdapter()
    _tts = ElevenLabsTTSAdapter()


async def get_store() -> SQLiteEventStore:
    await _store.connect()
    return _store


def get_clock() -> SimClock:
    return _clock


def get_llm() -> OllamaLLMProvider:
    return _llm


def get_orchestrator() -> SaathOrchestrator:
    return _orchestrator


def get_stt() -> WhisperSTTAdapter:
    return _stt


def get_tts() -> ElevenLabsTTSAdapter:
    return _tts


async def get_auth_context(
    x_house_id: str | None = Header(default=None),
    x_member_id: str | None = Header(default=None),
    store: SQLiteEventStore = Depends(get_store),
) -> AuthContext:
    """
    Enforces multi-tenant house authentication and member scoping:
    1. Rejects requests lacking X-House-Id with HTTP 400.
    2. Validates that the requested house exists (HTTP 404).
    3. If X-Member-Id is provided, enforces that the member strictly belongs to X-House-Id (HTTP 403).
    4. If X-Member-Id is omitted, defaults securely to the house's primary member.
    """
    if not x_house_id:
        raise ProblemDetailException(
            status_code=400,
            title="Missing House Scope",
            detail="Header 'X-House-Id' is required for house-scoped operations.",
        )

    house = await store.get_house(x_house_id)
    if not house:
        if x_house_id == "h-demo":
            # Auto-bootstrap demo house in clean/memory environments
            await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", 1000)
            await store.record_member("m-1", "h-demo", "You", None, "flatmate", ["me"], 1000)
            await store.record_member("m-2", "h-demo", "Rahul", "+919876543210", "flatmate", [], 1000)
            await store.record_member("m-3", "h-demo", "Amit", "+919876543211", "flatmate", [], 1000)
            house = await store.get_house("h-demo")
        else:
            raise ProblemDetailException(
                status_code=404,
                title="House Not Found",
                detail=f"House '{x_house_id}' does not exist.",
            )

    if x_member_id:
        member = await store.get_member(x_house_id, x_member_id)
        if not member:
            raise ProblemDetailException(
                status_code=403,
                title="Cross-House Actor Forbidden",
                detail=f"Member '{x_member_id}' does not belong to house '{x_house_id}'.",
            )
        return AuthContext(
            house_id=x_house_id,
            member_id=member["id"],
            member_name=member["name"],
            role=member.get("role", "flatmate"),
        )
    else:
        members = await store.get_members(x_house_id)
        if not members:
            raise ProblemDetailException(
                status_code=403,
                title="No House Members",
                detail=f"House '{x_house_id}' has no registered members.",
            )
        first = members[0]
        return AuthContext(
            house_id=x_house_id,
            member_id=first["id"],
            member_name=first["name"],
            role=first.get("role", "flatmate"),
        )


async def require_house_id(auth: AuthContext = Depends(get_auth_context)) -> str:
    """Convenience dependency returning verified house_id."""
    return auth.house_id
