"""FastAPI Main Application for SAATH with strict multi-house isolation and truthful integration."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, File, Form, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from saath.adapters.clock_sim import SimClock
from saath.adapters.store_sqlite import SQLiteEventStore
from saath.adapters.stt_whisper import WhisperSTTAdapter
from saath.api.deps import (
    AuthContext,
    get_auth_context,
    get_clock,
    get_llm,
    get_orchestrator,
    get_store,
    get_stt,
    get_tts,
    require_house_id,
)
from saath.adapters.tts_elevenlabs import ElevenLabsTTSAdapter
try:
    import sentry_sdk
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            send_default_pii=True,
            environment=os.environ.get("SAATH_ENV", "development"),
        )
except ImportError:
    pass
from saath.api.observability import ObservabilityMiddleware, get_latency_stats
from saath.api.errors import ProblemDetailException, problem_exception_handler
from saath.api.schemas import (
    AdvanceClockRequest,
    CommitmentReplyRequest,
    ConfirmExpenseRequest,
    IngestMessageRequest,
    OutboxSyncRequest,
)
from saath.application.orchestrator import SaathOrchestrator
from saath.domain.commitments import derive_next_action
from saath.domain.demo_seed import seed_household_checkpoint
from saath.domain.events import DomainEvent, EventType
from saath.domain.followup import Language, draft_followup
from saath.domain.ids import generate_uuidv7
from saath.domain.insights import aggregate_weekly_reflection, get_week_bounds


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize DB connection and seed default demo data if empty
    store = await get_store()
    clock = get_clock()
    llm = get_llm()

    # Warm up LLM in background/startup
    await llm.warmup()

    # Seed default flatmates for h-demo if not existing
    members = await store.get_members("h-demo")
    if not members:
        now_ms = clock.now_ms()
        await store.record_house("h-demo", "Indiranagar 3BHK", "Asia/Kolkata", now_ms)
        await store.record_member("m-1", "h-demo", "You", None, "flatmate", ["me"], now_ms)
        await store.record_member("m-2", "h-demo", "Rahul", "+919876543210", "flatmate", [], now_ms)
        await store.record_member("m-3", "h-demo", "Amit", "+919876543211", "flatmate", [], now_ms)
    yield
    await store.close()



app = FastAPI(
    title="SAATH API",
    description="Household memory and follow-through system",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS restricted to known local origins or environment configuration
_cors_origins_env = os.environ.get(
    "SAATH_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:8000",
)
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(ProblemDetailException, problem_exception_handler)
app.add_middleware(ObservabilityMiddleware)


# -------------------------------------------------------------
# Health and Diagnostics
# -------------------------------------------------------------
@app.get("/healthz", tags=["Diagnostics"])
async def healthz() -> dict[str, str]:
    return {"status": "ok", "app": "SAATH"}


@app.get("/sentry-debug", tags=["Diagnostics"])
async def sentry_debug():
    """Triggers a zero-division error to verify Sentry event capture."""
    division_by_zero = 1 / 0
    return {"result": division_by_zero}


@app.get("/metrics", tags=["Diagnostics"])
async def metrics() -> dict:
    """Pipeline latency stats (P50/P95/P99) for each sacred-loop stage."""
    return {"pipeline_latency_ms": get_latency_stats()}


@app.get("/readyz", tags=["Diagnostics"])
async def readyz(store: SQLiteEventStore = Depends(get_store)) -> dict[str, str]:
    """Readiness endpoint verifying actual database connectivity."""
    try:
        await store.get_all_events()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise ProblemDetailException(
            status_code=503, title="Service Unavailable", detail=str(e)
        ) from e


@app.get("/api/v1/clock", tags=["Diagnostics"])
async def get_clock_time(clock: SimClock = Depends(get_clock)) -> dict[str, Any]:
    """Returns system/simulated clock time and simulation status."""
    return {
        "now_ms": clock.now_ms(),
        "simulated": isinstance(clock, SimClock),
    }



# -------------------------------------------------------------
# Household Directory
# -------------------------------------------------------------
@app.get("/api/v1/house/members", tags=["House"])
async def get_house_members(
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
) -> dict[str, Any]:
    """Returns verified household members so UI displays real human names, not IDs."""
    members = await store.get_members(auth.house_id)
    return {
        "house_id": auth.house_id,
        "current_member_id": auth.member_id,
        "members": [
            {
                "id": m["id"],
                "name": m["name"],
                "phone": m.get("phone"),
                "role": m.get("role", "flatmate"),
                "aliases": m.get("aliases", []),
            }
            for m in members
        ],
    }


# -------------------------------------------------------------
# Ingestion
# -------------------------------------------------------------
@app.post("/api/v1/messages", tags=["Ingestion"])
async def ingest_message(
    req: IngestMessageRequest,
    auth: AuthContext = Depends(get_auth_context),
    orchestrator: SaathOrchestrator = Depends(get_orchestrator),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    now_ms = clock.now_ms()
    author_id = auth.member_id
    result = await orchestrator.ingest_message(
        house_id=auth.house_id,
        author_id=author_id,
        text=req.text,
        dedupe_key=req.dedupe_key,
        now_ms=now_ms,
        source=req.source,
    )
    return {
        "success": True,
        "message_id": result.message_id,
        "is_duplicate": result.is_duplicate,
        "applied_events": [
            {
                "id": ev.id,
                "type": ev.event_type.value,
                "event_type": ev.event_type.value,
                "payload": ev.payload,
                "confidence": ev.confidence,
            }
            for ev in result.applied_events
        ],
        "pending_confirmations": list(result.pending_confirmations),
        "reply_resolution": result.reply_resolution,
        "next_action": result.next_action,
        "parser": result.parser,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "fallback_reason": result.fallback_reason,
    }


MAX_AUDIO_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
}


@app.post("/api/v1/messages/voice", tags=["Ingestion"])
async def ingest_voice_message(
    file: UploadFile = File(...),
    author_id: str | None = Form(default=None),
    auth: AuthContext = Depends(get_auth_context),
    stt: WhisperSTTAdapter = Depends(get_stt),
    orchestrator: SaathOrchestrator = Depends(get_orchestrator),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    # 1. MIME Validation
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES and not content_type.startswith("audio/"):
        raise ProblemDetailException(
            status_code=415,
            title="Unsupported Media Type",
            detail=f"Audio type '{content_type}' is not supported. Use WAV, WebM, OGG, MP3 or M4A.",
        )

    # 2. File size validation (max 5 MB)
    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise ProblemDetailException(
            status_code=413,
            title="Payload Too Large",
            detail=f"Audio size {len(audio_bytes)} bytes exceeds maximum allowed limit of 5 MB.",
        )

    if len(audio_bytes) == 0:
        raise ProblemDetailException(
            status_code=400,
            title="Empty Audio",
            detail="Uploaded audio file cannot be empty.",
        )

    # 3. Audio signature / magic bytes validation
    is_valid_magic = (
        audio_bytes.startswith(b"RIFF")  # WAV
        or audio_bytes.startswith(b"\x1a\x45\xdf\xa3")  # WebM / Matroska
        or audio_bytes.startswith(b"OggS")  # OGG
        or audio_bytes.startswith(b"ID3")  # MP3 ID3v2
        or audio_bytes.startswith(b"\xff\xfb")  # MP3 frame sync
        or audio_bytes.startswith(b"\xff\xf3")
        or (len(audio_bytes) > 8 and audio_bytes[4:8] == b"ftyp")  # M4A / MP4
    )
    if not is_valid_magic:
        raise ProblemDetailException(
            status_code=415,
            title="Invalid Audio Format",
            detail="The uploaded file does not contain a valid audio signature (WAV, WebM, OGG, MP3, or M4A).",
        )

    # 4. Speech-to-text via singleton adapter
    transcribed_text = stt.transcribe(audio_bytes, filename=file.filename or "audio.wav")

    if not transcribed_text.strip():
        raise ProblemDetailException(
            status_code=422,
            title="Speech Unrecognized",
            detail="Voice could not be recognized. Please speak clearly or type your message.",
        )

    # 5. Route through identical ingestion pipeline
    now_ms = clock.now_ms()
    final_author_id = auth.member_id
    result = await orchestrator.ingest_message(
        house_id=auth.house_id,
        author_id=final_author_id,
        text=transcribed_text,
        dedupe_key=None,
        now_ms=now_ms,
        source="voice",
    )

    return {
        "success": True,
        "transcribed_text": transcribed_text,
        "message_id": result.message_id,
        "is_duplicate": result.is_duplicate,
        "applied_events": [
            {
                "id": ev.id,
                "type": ev.event_type.value,
                "event_type": ev.event_type.value,
                "payload": ev.payload,
                "confidence": ev.confidence,
            }
            for ev in result.applied_events
        ],
        "pending_confirmations": list(result.pending_confirmations),
        "reply_resolution": result.reply_resolution,
        "next_action": result.next_action,
        "parser": result.parser,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "fallback_reason": result.fallback_reason,
    }


# -------------------------------------------------------------
# Attention Screen
# -------------------------------------------------------------
@app.get("/api/v1/attention", tags=["Attention"])
async def get_attention(
    house_id: str = Depends(require_house_id),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    now_ms = clock.now_ms()
    open_commitments = await store.get_open_commitments(house_id)

    overdue_items: list[dict[str, Any]] = []
    waiting_items: list[dict[str, Any]] = []

    for c in open_commitments:
        na = derive_next_action(
            "commitment",
            {
                "id": c.id,
                "title": c.title,
                "responsible_party": c.responsible_party,
                "due_at": c.due_at,
            },
            is_overdue=c.is_overdue(now_ms),
        )
        c_dict = {
            "id": c.id,
            "title": c.title,
            "responsible_party": c.responsible_party,
            "promise_made_by": c.promise_made_by,
            "due_at": c.due_at,
            "state": c.state.value,
            "is_overdue": c.is_overdue(now_ms),
            "is_snoozed": c.is_snoozed(now_ms),
            "needs_attention": c.needs_attention(now_ms),
            "next_action": {"label": na.label, "kind": na.kind, "payload": na.payload}
            if na
            else None,
        }
        if c.needs_attention(now_ms):
            overdue_items.append(c_dict)
        else:
            waiting_items.append(c_dict)

    supplies = await store.get_depleted_supplies(house_id)
    supply_items = [
        {"id": s["id"], "item_name": s["item_name"], "status": s["status"]} for s in supplies
    ]

    return {
        "overdue": overdue_items,
        "waiting": waiting_items,
        "supplies_depleted": supply_items,
        "clock_ms": now_ms,
    }


# -------------------------------------------------------------
# Commitment Actions
# -------------------------------------------------------------
@app.get("/api/v1/commitments/{commitment_id}", tags=["Commitments"])
async def get_commitment(
    commitment_id: str,
    house_id: str = Depends(require_house_id),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    return {
        "commitment": {
            "id": c.id,
            "title": c.title,
            "promise_made_by": c.promise_made_by,
            "responsible_party": c.responsible_party,
            "tracked_by": c.tracked_by,
            "due_at": c.due_at,
            "state": c.state.value,
            "is_overdue": c.is_overdue(now_ms),
            "needs_attention": c.needs_attention(now_ms),
        }
    }


@app.post("/api/v1/commitments/{commitment_id}/done", tags=["Commitments"])
async def mark_commitment_done(
    commitment_id: str,
    payload: dict[str, Any] | None = None,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    actor_id = auth.member_id
    if payload and payload.get("actor_id"):
        candidate_actor = str(payload["actor_id"])
        if not await store.validate_member_belongs_to_house(auth.house_id, candidate_actor):
            raise ProblemDetailException(
                status_code=403,
                title="Forbidden",
                detail=f"Actor '{candidate_actor}' does not belong to house '{auth.house_id}'",
            )
        actor_id = candidate_actor

    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id=actor_id,
        occurred_at=now_ms,
        payload={"commitment_id": commitment_id, "new_state": "done", "actor_id": actor_id},
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "state": "done"}


@app.post("/api/v1/commitments/{commitment_id}/snooze", tags=["Commitments"])
async def snooze_commitment(
    commitment_id: str,
    payload: dict[str, Any],
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    actor_id = auth.member_id
    if payload.get("actor_id"):
        candidate_actor = str(payload["actor_id"])
        if not await store.validate_member_belongs_to_house(auth.house_id, candidate_actor):
            raise ProblemDetailException(
                status_code=403,
                title="Forbidden",
                detail=f"Actor '{candidate_actor}' does not belong to house '{auth.house_id}'",
            )
        actor_id = candidate_actor

    duration_hours = int(payload.get("duration_hours", 24))
    until_ms = now_ms + (duration_hours * 3600 * 1000)
    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id=actor_id,
        occurred_at=now_ms,
        payload={
            "commitment_id": commitment_id,
            "new_state": "waiting",
            "snoozed_until": until_ms,
            "actor_id": actor_id,
        },
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "snoozed_until": until_ms}


@app.post("/api/v1/commitments/{commitment_id}/reschedule", tags=["Commitments"])
async def reschedule_commitment(
    commitment_id: str,
    payload: dict[str, Any],
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    new_due_at = int(payload.get("new_due_at", now_ms + 86400000))
    if new_due_at <= now_ms:
        raise ProblemDetailException(
            status_code=422,
            title="Invalid Due Date",
            detail="Rescheduled due date must strictly be in the future relative to current time.",
        )
    actor_id = auth.member_id
    if payload.get("actor_id"):
        candidate_actor = str(payload["actor_id"])
        if not await store.validate_member_belongs_to_house(auth.house_id, candidate_actor):
            raise ProblemDetailException(
                status_code=403,
                title="Forbidden",
                detail=f"Actor '{candidate_actor}' does not belong to house '{auth.house_id}'",
            )
        actor_id = candidate_actor

    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id=actor_id,
        occurred_at=now_ms,
        payload={
            "commitment_id": commitment_id,
            "new_state": "rescheduled",
            "new_due_at": new_due_at,
            "actor_id": actor_id,
        },
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "new_due_at": new_due_at}


@app.post("/api/v1/commitments/{commitment_id}/cancel", tags=["Commitments"])
async def cancel_commitment(
    commitment_id: str,
    payload: dict[str, Any] | None = None,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    actor_id = auth.member_id
    if payload and payload.get("actor_id"):
        candidate_actor = str(payload["actor_id"])
        if not await store.validate_member_belongs_to_house(auth.house_id, candidate_actor):
            raise ProblemDetailException(
                status_code=403,
                title="Forbidden",
                detail=f"Actor '{candidate_actor}' does not belong to house '{auth.house_id}'",
            )
        actor_id = candidate_actor

    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.COMMITMENT_UPDATED,
        actor_id=actor_id,
        occurred_at=now_ms,
        payload={"commitment_id": commitment_id, "new_state": "cancelled", "actor_id": actor_id},
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "state": "cancelled"}


@app.post("/api/v1/commitments/{commitment_id}/reply", tags=["Commitments"])
async def reply_commitment(
    commitment_id: str,
    req: CommitmentReplyRequest,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    actor_id = auth.member_id
    if req.actor_id:
        if not await store.validate_member_belongs_to_house(auth.house_id, req.actor_id):
            raise ProblemDetailException(
                status_code=403,
                title="Forbidden",
                detail=f"Actor '{req.actor_id}' does not belong to house '{auth.house_id}'",
            )
        actor_id = req.actor_id

    intent = req.intent.lower().strip()
    if intent == "done":
        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id=auth.house_id,
            event_type=EventType.COMMITMENT_UPDATED,
            actor_id=actor_id,
            occurred_at=now_ms,
            payload={"commitment_id": commitment_id, "new_state": "done", "actor_id": actor_id},
        )
        await store.append_event_and_project(ev)
        return {"success": True, "commitment_id": commitment_id, "intent": intent, "state": "done"}

    elif intent == "cancelled":
        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id=auth.house_id,
            event_type=EventType.COMMITMENT_UPDATED,
            actor_id=actor_id,
            occurred_at=now_ms,
            payload={"commitment_id": commitment_id, "new_state": "cancelled", "actor_id": actor_id},
        )
        await store.append_event_and_project(ev)
        return {"success": True, "commitment_id": commitment_id, "intent": intent, "state": "cancelled"}

    elif intent == "rescheduled":
        # Resolve due date
        new_due_at = now_ms + (24 * 3600 * 1000)  # default tomorrow (+24h)
        if isinstance(req.new_due, int):
            new_due_at = req.new_due
        elif isinstance(req.new_due, str) and req.new_due.isdigit():
            new_due_at = int(req.new_due)

        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id=auth.house_id,
            event_type=EventType.COMMITMENT_UPDATED,
            actor_id=actor_id,
            occurred_at=now_ms,
            payload={
                "commitment_id": commitment_id,
                "new_state": "rescheduled",
                "new_due_at": new_due_at,
                "actor_id": actor_id,
            },
        )
        await store.append_event_and_project(ev)
        return {
            "success": True,
            "commitment_id": commitment_id,
            "intent": intent,
            "state": "rescheduled",
            "new_due_at": new_due_at,
        }

    elif intent == "not_yet":
        # Keeps state as waiting, optionally records action log
        return {"success": True, "commitment_id": commitment_id, "intent": intent, "state": c.state.value}

    else:
        raise ProblemDetailException(
            status_code=422,
            title="Invalid Reply Intent",
            detail=f"Intent '{req.intent}' is not valid. Must be one of: not_yet, rescheduled, done, cancelled.",
        )



@app.post("/api/v1/commitments/{commitment_id}/followup", tags=["Commitments"])
async def create_followup_draft(
    commitment_id: str,
    lang: str = Query(default="hinglish"),
    phone: str | None = Query(default=None),
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()

    # Look up verified phone of responsible party from house members directory if not explicitly provided
    target_phone = phone
    if not target_phone:
        members = await store.get_members(auth.house_id)
        for m in members:
            if (
                m["name"].lower() == c.responsible_party.lower()
                or c.responsible_party.lower() in [a.lower() for a in m.get("aliases", [])]
            ):
                target_phone = m.get("phone")
                break

    language_enum = Language(lang) if lang in [e.value for e in Language] else Language.HINGLISH
    draft = draft_followup(c, lang=language_enum, phone_number=target_phone, now_ms=now_ms)

    # Persist follow-up drafted event to update projection
    ev_draft = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.FOLLOWUP_DRAFTED,
        actor_id=auth.member_id,
        occurred_at=now_ms,
        payload={
            "followup_id": generate_uuidv7("fu"),
            "commitment_id": commitment_id,
            "draft_text": draft.draft_text,
            "whatsapp_url": draft.whatsapp_url,
        },
    )
    await store.append_event_and_project(ev_draft)

    return {
        "draft": {
            "commitment_id": draft.commitment_id,
            "status": draft.status.value,
            "draft_text": draft.draft_text,
            "whatsapp_url": draft.whatsapp_url,
            "lang": draft.lang.value,
        }
    }


@app.post("/api/v1/commitments/{commitment_id}/voice_followup", tags=["Commitments"])
async def create_voice_followup_draft(
    commitment_id: str,
    lang: str = Query(default="hinglish"),
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
    tts: ElevenLabsTTSAdapter = Depends(get_tts),
) -> dict[str, Any]:
    """Generates audio spoken speech check-in via ElevenLabs for the commitment."""
    c = await store.get_commitment_by_id(commitment_id, house_id=auth.house_id)
    if not c:
        raise ProblemDetailException(
            status_code=404, title="Not Found", detail="Commitment not found in this house"
        )
    now_ms = clock.now_ms()
    language_enum = Language(lang) if lang in [e.value for e in Language] else Language.HINGLISH
    draft = draft_followup(c, lang=language_enum, now_ms=now_ms)
    voice_data = await tts.generate_speech_data_uri(draft.draft_text)
    return {
        "success": True,
        "commitment_id": commitment_id,
        "draft_text": draft.draft_text,
        "voice": voice_data,
    }


@app.post("/api/v1/followups/{commitment_id}/opened", tags=["Commitments"])
async def mark_followup_opened(
    commitment_id: str,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    """Records that the WhatsApp follow-up link was opened by a member."""
    now_ms = clock.now_ms()
    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.FOLLOWUP_OPENED,
        actor_id=auth.member_id,
        occurred_at=now_ms,
        payload={
            "commitment_id": commitment_id,
            "channel": "whatsapp",
        },
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "status": "opened"}


@app.post("/api/v1/followups/{commitment_id}/sent", tags=["Commitments"])
async def mark_followup_sent(
    commitment_id: str,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    """Records explicit confirmation that the follow-up message was sent."""
    now_ms = clock.now_ms()
    ev = DomainEvent(
        id=generate_uuidv7("ev"),
        house_id=auth.house_id,
        event_type=EventType.FOLLOWUP_SENT,
        actor_id=auth.member_id,
        occurred_at=now_ms,
        payload={
            "commitment_id": commitment_id,
            "followup_id": generate_uuidv7("fu"),
            "channel": "whatsapp",
        },
    )
    await store.append_event_and_project(ev)
    return {"success": True, "commitment_id": commitment_id, "sent_at": now_ms}


@app.get("/api/v1/expenses", tags=["Expenses"])
async def get_expenses(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
) -> dict[str, Any]:
    """Fetches expenses for the household with optional status filter (pending vs confirmed)."""
    expenses = await store.get_expenses(auth.house_id, status=status, limit=limit)
    return {"expenses": expenses, "total": len(expenses)}


@app.post("/api/v1/events/confirm", tags=["Events"])
@app.post("/api/v1/expenses/confirm", tags=["Expenses"])

async def confirm_event(
    req: ConfirmExpenseRequest,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    orchestrator: SaathOrchestrator = Depends(get_orchestrator),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    """
    Confirms an extracted expense split.
    Enforces that payer and all participants belong to the house,
    validates that sum(shares) == amount_paise, and ensures idempotency.
    """
    house_id = auth.house_id
    now_ms = clock.now_ms()

    # 1. Validate payer and participants strictly belong to house
    if not await store.validate_member_belongs_to_house(house_id, req.paid_by):
        raise ProblemDetailException(
            status_code=403,
            title="Invalid Payer",
            detail=f"Payer '{req.paid_by}' does not belong to house '{house_id}'.",
        )
    for pid in req.participant_ids:
        if not await store.validate_member_belongs_to_house(house_id, pid):
            raise ProblemDetailException(
                status_code=403,
                title="Invalid Participant",
                detail=f"Participant '{pid}' does not belong to house '{house_id}'.",
            )

    # 2. Validate exact sum invariant
    if sum(req.shares.values()) != req.amount_paise:
        raise ProblemDetailException(
            status_code=422,
            title="Split Sum Mismatch",
            detail=f"Sum of shares ({sum(req.shares.values())} paise) must exactly equal total amount ({req.amount_paise} paise).",
        )

    # 3. Double-click idempotency protection
    if await store.has_confirmed_expense(house_id, req.expense_id):
        return {
            "success": True,
            "status": "already_confirmed",
            "already_confirmed": True,
            "expense_id": req.expense_id,
        }

    ev = await orchestrator.confirm_expense(
        house_id=house_id,
        author_id=auth.member_id,
        payload=req.model_dump(),
        now_ms=now_ms,
    )
    return {
        "success": True,
        "event_id": ev.id,
        "status": "confirmed",
        "already_confirmed": False,
    }


@app.post("/api/v1/events/{event_id}/undo", tags=["Events"])
async def undo_event(
    event_id: str,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    """
    Reverts an event by appending a superseding EVENT_SUPERSEDED event
    and atomically rebuilding projections to preserve exact replay equivalence.
    """
    now_ms = clock.now_ms()
    try:
        undo_ev = await store.undo_event(
            house_id=auth.house_id,
            event_id=event_id,
            actor_id=auth.member_id,
            now_ms=now_ms,
        )
        return {
            "success": True,
            "superseding_event_id": undo_ev.id,
            "target_event_id": event_id,
            "status": "superseded",
        }
    except ValueError as e:
        raise ProblemDetailException(
            status_code=400, title="Cannot Undo Event", detail=str(e)
        ) from e


# -------------------------------------------------------------
# Weekly Reflection & History
# -------------------------------------------------------------
@app.get("/api/v1/reflection", tags=["Reflection"])
async def get_weekly_reflection(
    week_timestamp: int | None = Query(default=None),
    house_id: str = Depends(require_house_id),
    store: SQLiteEventStore = Depends(get_store),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    now_ms = week_timestamp or clock.now_ms()
    week_start, week_end = get_week_bounds(now_ms, "Asia/Kolkata")

    members = await store.get_members(house_id)
    member_names = {m["id"]: m["name"] for m in members}
    actions = await store.get_weekly_action_records(house_id, week_start, week_end)

    reflection = aggregate_weekly_reflection(actions, member_names, week_start, week_end)
    return {
        "week_start_ms": reflection.week_start_ms,
        "week_end_ms": reflection.week_end_ms,
        "rebalance_suggestion": reflection.rebalance_suggestion,
        "members": [
            {
                "member_id": s.member_id,
                "name": s.member_name,
                "physical_count": s.physical_count,
                "coordination_count": s.coordination_count,
                "breakdown": s.breakdown_by_label,
            }
            for s in reflection.summaries.values()
        ],
    }


@app.get("/api/v1/history", tags=["History"])
async def get_event_history(
    limit: int = Query(default=100, ge=1, le=1000),
    house_id: str = Depends(require_house_id),
    store: SQLiteEventStore = Depends(get_store),
) -> dict[str, Any]:
    events = await store.get_all_events(house_id=house_id)
    # Apply limit
    limited = events[:limit]
    return {
        "total": len(events),
        "events": [
            {
                "id": ev.id,
                "type": ev.event_type.value,
                "actor_id": ev.actor_id,
                "payload": ev.payload,
                "occurred_at": ev.occurred_at,
                "status": ev.status,
            }
            for ev in limited
        ],
    }


# -------------------------------------------------------------
# Offline Outbox Sync (PWA)
# -------------------------------------------------------------
@app.post("/api/v1/sync/outbox", tags=["Offline Sync"])
async def sync_outbox(
    req: OutboxSyncRequest,
    auth: AuthContext = Depends(get_auth_context),
    store: SQLiteEventStore = Depends(get_store),
    orchestrator: SaathOrchestrator = Depends(get_orchestrator),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    """
    Idempotent sync endpoint for the client-side PWA outbox.
    Each item is keyed by (house_id, client_uuid) preventing duplicate ingestion.
    """
    results: list[dict[str, Any]] = []
    now_ms = clock.now_ms()

    for item in req.items:
        # Check idempotency receipt
        is_new = await store.record_outbox_receipt(
            client_uuid=item.client_uuid,
            house_id=auth.house_id,
            message_id=None,
            now_ms=now_ms,
        )
        if not is_new:
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "status": "duplicate",
                    "message_id": None,
                    "error": None,
                }
            )
            continue

        try:
            res = await orchestrator.ingest_message(
                house_id=auth.house_id,
                author_id=auth.member_id,
                text=item.text,
                dedupe_key=item.client_uuid,
                now_ms=item.occurred_at or now_ms,
                source="outbox_sync",
            )
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "status": "applied",
                    "message_id": res.message_id,
                    "error": None,
                }
            )
        except Exception as e:
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "status": "failed",
                    "message_id": None,
                    "error": str(e),
                }
            )

    return {
        "synced_count": sum(1 for r in results if r["status"] == "applied"),
        "items": results,
    }


# -------------------------------------------------------------
# Demo Clock Manipulation
# -------------------------------------------------------------
@app.post("/api/v1/demo/clock/advance", tags=["Demo"])
async def advance_demo_clock(
    req: AdvanceClockRequest,
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    if req.target_ms is not None:
        clock.set_ms(req.target_ms)
    else:
        delta_ms = int(req.delta_hours * 3600 * 1000)
        clock.advance_ms(delta_ms)
    return {"new_clock_ms": clock.now_ms()}


@app.post("/api/v1/demo/seed", tags=["Demo"])
async def seed_demo_data(
    checkpoint: str = Query(default="monday_morning"),
    house_id: str = Depends(require_house_id),
    store: SQLiteEventStore = Depends(get_store),
    orchestrator: SaathOrchestrator = Depends(get_orchestrator),
    clock: SimClock = Depends(get_clock),
) -> dict[str, Any]:
    now_ms = clock.now_ms()
    return await seed_household_checkpoint(
        checkpoint=checkpoint,
        house_id=house_id,
        store=store,
        orchestrator=orchestrator,
        now_ms=now_ms,
    )



from fastapi.responses import FileResponse

# Mount Web Client static files & SPA fallback routing for Render
_dist_path = Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist"
if _dist_path.exists():
    _index_path = _dist_path / "index.html"
    app.mount("/assets", StaticFiles(directory=str(_dist_path / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("healthz") or full_path.startswith("metrics") or full_path.startswith("sentry-debug"):
            raise ProblemDetailException(status_code=404, title="Not Found", detail=f"Endpoint '{full_path}' not found")
        file_path = _dist_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_index_path))
