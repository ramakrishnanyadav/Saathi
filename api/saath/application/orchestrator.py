"""Application orchestrator connecting domain, event store, and LLM provider."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from saath.adapters.store_sqlite import SQLiteEventStore
from saath.application.validator import validate_extracted_event
from saath.application.verifier import verify_event_against_source
from saath.domain.commitments import derive_next_action, resolve_reply
from saath.domain.events import ActionKind, DomainEvent, EventType
from saath.domain.ids import generate_uuidv7
from saath.domain.money import split_equally
from saath.domain.timeparse import resolve_symbolic_time
from saath.ports.llm import HouseContext, LLMProvider


@dataclass(frozen=True, slots=True)
class IngestResult:
    message_id: str
    is_duplicate: bool
    applied_events: tuple[DomainEvent, ...]
    pending_confirmations: tuple[dict[str, Any], ...]
    reply_resolution: dict[str, Any] | None
    next_action: dict[str, Any] | None
    parser: str = "rules"
    model: str = "rules_engine"
    latency_ms: float = 0.0
    fallback_reason: str | None = None



class SaathOrchestrator:
    """Core application service orchestrating message ingestion, confirmation, and replay."""

    def __init__(self, store: SQLiteEventStore, llm_provider: LLMProvider) -> None:
        self.store = store
        self.llm = llm_provider

    async def ingest_message(
        self,
        house_id: str,
        author_id: str,
        text: str,
        dedupe_key: str | None = None,
        now_ms: int | None = None,
        source: str = "text",
    ) -> IngestResult:
        """
        Executes the end-to-end ingestion pipeline:
        Dedupe -> Context -> Extract -> Validate -> Verify -> Resolve Time -> Money Split -> Route -> Apply
        """
        if now_ms is None:
            now_ms = int(time.time() * 1000)

        msg_id = generate_uuidv7("msg")
        actual_dedupe_key = dedupe_key or msg_id

        # 1. Deduplication
        is_new = await self.store.record_message(
            message_id=msg_id,
            house_id=house_id,
            author_id=author_id,
            text=text,
            dedupe_key=actual_dedupe_key,
            received_at=now_ms,
            source=source,
        )
        if not is_new:
            return IngestResult(
                message_id=msg_id,
                is_duplicate=True,
                applied_events=(),
                pending_confirmations=(),
                reply_resolution=None,
                next_action=None,
            )

        # 2. Build Context
        members = await self.store.get_members(house_id)
        open_commitments = await self.store.get_open_commitments(house_id)
        context = HouseContext(
            house_id=house_id,
            author_id=author_id,
            timezone="Asia/Kolkata",
            members=members,
            open_commitments=[
                {"id": c.id, "title": c.title, "state": c.state.value} for c in open_commitments
            ],
            recent_events=(),
            now_ms=now_ms,
        )

        # 3. Check for Short Reply first
        if open_commitments:
            reply_res = resolve_reply(
                text=text,
                open_commitments=open_commitments,
                now_ms=now_ms,
                house_tz_str="Asia/Kolkata",
            )
            if reply_res.intent.value != "unrelated" and (
                reply_res.target_commitment or reply_res.ask_which_candidates
            ):
                # We have a valid reply!
                applied: list[DomainEvent] = []
                if reply_res.target_commitment:
                    target = reply_res.target_commitment
                    # Emit commitment_updated event
                    new_state = (
                        "done"
                        if reply_res.intent.value in ("done", "someone_else_did")
                        else (
                            "rescheduled"
                            if reply_res.intent.value == "rescheduled"
                            else (
                                "cancelled" if reply_res.intent.value == "cancelled" else "waiting"
                            )
                        )
                    )
                    ev_update = DomainEvent(
                        id=generate_uuidv7("ev"),
                        house_id=house_id,
                        event_type=EventType.COMMITMENT_UPDATED,
                        actor_id=author_id,
                        occurred_at=now_ms,
                        payload={
                            "commitment_id": target.id,
                            "new_state": new_state,
                            "new_due_at": reply_res.new_due_at,
                            "note": text,
                        },
                        message_id=msg_id,
                    )
                    applied.append(ev_update)

                    # If someone else did it, credit them with action_taken
                    if reply_res.intent.value == "someone_else_did" and reply_res.acting_member:
                        credited_member_id = author_id
                        target_name = reply_res.acting_member.lower().strip()
                        for m in members:
                            m_name = m["name"].lower().strip()
                            m_aliases = [a.lower().strip() for a in m.get("aliases", [])]
                            if target_name == m_name or target_name in m_aliases:
                                credited_member_id = m["id"]
                                break
                        ev_action = DomainEvent(
                            id=generate_uuidv7("ev"),
                            house_id=house_id,
                            event_type=EventType.ACTION_TAKEN,
                            actor_id=author_id,
                            occurred_at=now_ms,
                            payload={
                                "member_id": credited_member_id,
                                "kind": ActionKind.COORDINATION.value,
                                "label": f"Resolved: {target.title}",
                                "details": text,
                                "commitment_id": target.id,
                            },
                            message_id=msg_id,
                        )
                        applied.append(ev_action)

                    # Commit all derived reply events atomically in a single transaction
                    await self.store.append_events_and_project_batch(applied)

                reply_info = {
                    "intent": reply_res.intent.value,
                    "target_commitment_id": reply_res.target_commitment.id
                    if reply_res.target_commitment
                    else None,
                    "acting_member": reply_res.acting_member,
                    "ask_which": [
                        {"id": c.commitment_id, "title": c.title}
                        for c in reply_res.ask_which_candidates
                    ],
                    "ask_which_candidates": [
                        {"id": c.commitment_id, "title": c.title}
                        for c in reply_res.ask_which_candidates
                    ],
                }
                return IngestResult(
                    message_id=msg_id,
                    is_duplicate=False,
                    applied_events=tuple(applied),
                    pending_confirmations=(),
                    reply_resolution=reply_info,
                    next_action=None,
                    parser="rules",
                    model="rules_engine",
                    latency_ms=0.1,
                    fallback_reason=None,
                )

        # 4. Extract Events via LLM / Fallback
        extraction = await self.llm.extract_events(text, context)
        valid_member_ids = [m["id"] for m in members] if members else [author_id]

        applied_events: list[DomainEvent] = []
        pending_confirmations: list[dict[str, Any]] = []

        for raw_ev in extraction.events:
            # 5. Validate
            etype, val_payload = validate_extracted_event(
                raw_ev.event_type, raw_ev.payload, valid_member_ids
            )

            # 6. Verify against source text
            verified_conf = verify_event_against_source(etype, val_payload, text, raw_ev.confidence)

            # 7. Resolve relative dates
            if etype == EventType.COMMITMENT_CREATED:
                if "symbolic_due" in val_payload and val_payload["symbolic_due"]:
                    due_ms = resolve_symbolic_time(
                        val_payload["symbolic_due"], now_ms, "Asia/Kolkata"
                    )
                    val_payload["due_at"] = due_ms
                    val_payload.pop("symbolic_due", None)
                elif "due_at" not in val_payload:
                    val_payload["due_at"] = None

            # 8. Money Split Calculation
            if etype == EventType.EXPENSE_CREATED:
                if not val_payload.get("expense_id"):
                    val_payload["expense_id"] = generate_uuidv7("exp")
                amt = int(val_payload["amount_paise"])
                pids = val_payload.get("participant_ids") or tuple(valid_member_ids)
                split_res = split_equally(amt, pids)
                val_payload["shares"] = split_res.shares

                # CRITICAL RULE: Money events ALWAYS require explicit confirmation
                pending_confirmations.append(
                    {
                        "type": "expense_confirmation",
                        "title": val_payload.get("title", "Expense"),
                        "amount_paise": amt,
                        "paid_by": val_payload.get("paid_by", author_id),
                        "shares": split_res.shares,
                        "payload": val_payload,
                    }
                )
                continue

            if etype == EventType.COMMITMENT_CREATED and not val_payload.get("commitment_id"):
                val_payload["commitment_id"] = generate_uuidv7("comm")
            elif etype == EventType.ISSUE_REPORTED and not val_payload.get("issue_id"):
                val_payload["issue_id"] = generate_uuidv7("issue")
            elif etype == EventType.EXPENSE_CREATED and not val_payload.get("expense_id"):
                val_payload["expense_id"] = generate_uuidv7("exp")
            elif etype in (EventType.SUPPLY_DEPLETED, EventType.SUPPLY_RESTOCKED) and not val_payload.get("supply_id"):
                val_payload["supply_id"] = generate_uuidv7("sup")
            elif etype == EventType.ACTION_TAKEN and not val_payload.get("action_id"):
                val_payload["action_id"] = generate_uuidv7("act")

            # Stage verified non-money event with full AI provenance
            ev_obj = DomainEvent(
                id=generate_uuidv7("ev"),
                house_id=house_id,
                event_type=etype,
                actor_id=author_id,
                occurred_at=now_ms,
                payload=val_payload,
                message_id=msg_id,
                causation_id=msg_id,             # this event was caused by this message
                correlation_id=msg_id,           # all events from this message share correlation
                source_message=text,             # raw user text — auditable AI provenance
                validation_status="fallback" if extraction.used_fallback else "validated",
                used_fallback=extraction.used_fallback,
                confidence=verified_conf,
            )
            applied_events.append(ev_obj)

        # Atomic commit: all derived events from this message persisted together
        if applied_events:
            await self.store.append_events_and_project_batch(applied_events)

        # 9. Derive next action
        next_action_obj = None
        if applied_events:
            first_ev = applied_events[0]
            if first_ev.event_type == EventType.COMMITMENT_CREATED:
                na = derive_next_action(
                    "commitment",
                    {
                        "id": first_ev.payload.get("commitment_id", first_ev.id),
                        "responsible_party": first_ev.payload.get("responsible_party", "someone"),
                    },
                    is_overdue=False,
                )
                if na:
                    next_action_obj = {"label": na.label, "kind": na.kind, "payload": na.payload}
            elif first_ev.event_type == EventType.SUPPLY_DEPLETED:
                na = derive_next_action(
                    "supply",
                    {
                        "item_name": first_ev.payload.get("item_name", "supplies"),
                        "status": "depleted",
                    },
                )
                if na:
                    next_action_obj = {"label": na.label, "kind": na.kind, "payload": na.payload}

        return IngestResult(
            message_id=msg_id,
            is_duplicate=False,
            applied_events=tuple(applied_events),
            pending_confirmations=tuple(pending_confirmations),
            reply_resolution=None,
            next_action=next_action_obj,
            parser=extraction.parser,
            model=extraction.model,
            latency_ms=extraction.latency_ms,
            fallback_reason=extraction.fallback_reason,
        )

    async def confirm_expense(
        self, house_id: str, author_id: str, payload: dict[str, Any], now_ms: int | None = None
    ) -> DomainEvent:
        """Applies an expense after human confirmation."""
        if now_ms is None:
            now_ms = int(time.time() * 1000)

        ev = DomainEvent(
            id=generate_uuidv7("ev"),
            house_id=house_id,
            event_type=EventType.EXPENSE_CREATED,
            actor_id=author_id,
            occurred_at=now_ms,
            payload={**payload, "is_confirmed": True},
        )
        await self.store.append_event_and_project(ev)
        return ev
