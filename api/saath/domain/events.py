"""Domain event types and immutable payload dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class EventType(str, Enum):
    ISSUE_REPORTED = "issue_reported"
    COMMITMENT_CREATED = "commitment_created"
    COMMITMENT_UPDATED = "commitment_updated"
    EXPENSE_CREATED = "expense_created"
    EXPENSE_CONFIRMED = "expense_confirmed"
    SUPPLY_DEPLETED = "supply_depleted"
    SUPPLY_RESTOCKED = "supply_restocked"
    ACTION_TAKEN = "action_taken"
    FOLLOWUP_DRAFTED = "followup_drafted"
    FOLLOWUP_OPENED = "followup_opened"
    FOLLOWUP_SENT = "followup_sent"
    NOTE_RECORDED = "note_recorded"
    EVENT_SUPERSEDED = "event_superseded"


class ActionKind(str, Enum):
    PHYSICAL = "physical"
    COORDINATION = "coordination"


class CommitmentState(str, Enum):
    WAITING = "waiting"
    DONE = "done"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class IssueReportedPayload:
    title: str
    category: str = "general"
    description: str = ""
    urgency: str = "normal"


@dataclass(frozen=True, slots=True)
class CommitmentCreatedPayload:
    title: str
    promise_made_by: str
    responsible_party: str
    tracked_by: str
    due_at: int | None = None  # UTC epoch milliseconds, optional if unknown
    issue_id: str | None = None
    snoozed_until: int | None = None


@dataclass(frozen=True, slots=True)
class CommitmentUpdatedPayload:
    commitment_id: str
    new_state: CommitmentState
    new_due_at: int | None = None
    snoozed_until: int | None = None
    note: str = ""
    actor_id: str | None = None


@dataclass(frozen=True, slots=True)
class ExpenseCreatedPayload:
    title: str
    amount_paise: int
    paid_by: str
    participant_ids: tuple[str, ...]
    shares: Mapping[str, int]
    is_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class ExpenseConfirmedPayload:
    expense_id: str
    confirmed_by: str


@dataclass(frozen=True, slots=True)
class SupplyDepletedPayload:
    item_name: str
    item_norm: str
    reported_by: str


@dataclass(frozen=True, slots=True)
class SupplyRestockedPayload:
    item_name: str
    item_norm: str
    restocked_by: str


@dataclass(frozen=True, slots=True)
class ActionTakenPayload:
    member_id: str
    kind: ActionKind
    label: str
    details: str = ""
    issue_id: str | None = None
    commitment_id: str | None = None


@dataclass(frozen=True, slots=True)
class FollowupSentPayload:
    commitment_id: str
    followup_id: str
    channel: str = "whatsapp"


@dataclass(frozen=True, slots=True)
class NoteRecordedPayload:
    text: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Immutable domain event with full causality chain and AI provenance.

    Causality chain answers: "Why does this event exist?"
      expense_paid → commitment_made → commitment_overdue → followup_draft_ready

    Provenance answers: "What AI fact produced this, and how confident are we?"
      You said: 'Amit will call the plumber tomorrow'
      SAATH understood: Amit → call plumber → tomorrow (confidence=0.9, validated)
    """

    id: str
    house_id: str
    event_type: EventType
    actor_id: str
    occurred_at: int  # UTC epoch milliseconds
    payload: Mapping[str, Any]
    message_id: str | None = None
    # Causality chain
    causation_id: str | None = None     # direct cause event_id or message_id
    correlation_id: str | None = None   # logical conversation / flow grouping
    # AI provenance — every AI-generated fact retains its origin
    source_message: str | None = None   # raw user text that produced this event
    extracted_field: str | None = None  # field in extraction (e.g. 'responsible_party')
    validation_status: str = "validated"  # validated | rejected | fallback
    used_fallback: bool = False         # True when rule parser was used instead of LLM
    # Immutability and audit
    confidence: float = 1.0
    status: str = "applied"
    supersedes_id: str | None = None
    schema_version: int = 1
