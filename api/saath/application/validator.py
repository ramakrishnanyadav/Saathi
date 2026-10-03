"""Validation engine with strict Pydantic schemas for extracted candidate events."""

from __future__ import annotations

from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from saath.domain.events import ActionKind, EventType
from saath.domain.money import MAX_PAISE, MIN_PAISE


class ExtractionValidationError(Exception):
    """Raised when an extracted candidate fails safety validation."""


class CommitmentCreatedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    responsible_party: str = Field(min_length=1)
    commitment_id: str | None = None
    promise_made_by: str | None = None
    tracked_by: str | None = None
    due_at: int | None = None
    symbolic_due: dict[str, Any] | None = None
    issue_id: str | None = None
    snoozed_until: int | None = None


class IssueReportedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    issue_id: str | None = None
    category: str = "general"
    description: str = ""
    urgency: str = "normal"


class ExpenseCreatedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    amount_paise: int = Field(ge=MIN_PAISE, le=MAX_PAISE)
    expense_id: str | None = None
    paid_by: str | None = None
    participant_ids: Sequence[str] | None = None
    shares: dict[str, int] | None = None
    is_confirmed: bool = False
    category: str | None = None
    description: str | None = None


class SupplyDepletedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_name: str = Field(min_length=1)
    supply_id: str | None = None
    item_norm: str | None = None
    reported_by: str | None = None


class SupplyRestockedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_name: str = Field(min_length=1)
    supply_id: str | None = None
    item_norm: str | None = None
    restocked_by: str | None = None


class ActionTakenSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1)
    action_id: str | None = None
    kind: str = "coordination"
    details: str = ""
    member_id: str | None = None
    issue_id: str | None = None
    commitment_id: str | None = None


class NoteRecordedSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    tags: Sequence[str] = ()


def validate_extracted_event(
    event_type: str,
    payload: dict[str, Any],
    valid_member_ids: Sequence[str],
) -> tuple[EventType, dict[str, Any]]:
    """
    Validates candidate event against security allow-lists, Pydantic schemas, and domain invariants:
    1. Event type must be a valid known EventType.
    2. Any participant, author, or member ID must strictly belong to valid_member_ids (no silent substitution).
    3. Strict Pydantic payload models enforce required fields and constraints.
    4. Money amounts must be strictly within [MIN_PAISE, MAX_PAISE].
    """
    # 1. Validate EventType
    try:
        etype = EventType(event_type)
    except ValueError:
        raise ExtractionValidationError(f"Invalid event_type '{event_type}'") from None

    # 2. Strict Schema Validation per EventType
    try:
        if etype == EventType.COMMITMENT_CREATED:
            parsed_comm = CommitmentCreatedSchema.model_validate(payload)
            validated_payload = parsed_comm.model_dump()
            if not validated_payload.get("promise_made_by"):
                validated_payload["promise_made_by"] = validated_payload["responsible_party"]

        elif etype == EventType.ISSUE_REPORTED:
            parsed_issue = IssueReportedSchema.model_validate(payload)
            validated_payload = parsed_issue.model_dump()

        elif etype == EventType.EXPENSE_CREATED:
            parsed_exp = ExpenseCreatedSchema.model_validate(payload)
            validated_payload = parsed_exp.model_dump()
            # Invariant: Extracted expense is NEVER auto-confirmed
            validated_payload["is_confirmed"] = False

        elif etype == EventType.SUPPLY_DEPLETED:
            parsed_sup = SupplyDepletedSchema.model_validate(payload)
            validated_payload = parsed_sup.model_dump()
            if not validated_payload.get("item_norm"):
                validated_payload["item_norm"] = validated_payload["item_name"].lower().replace(" ", "_")

        elif etype == EventType.SUPPLY_RESTOCKED:
            parsed_restock = SupplyRestockedSchema.model_validate(payload)
            validated_payload = parsed_restock.model_dump()
            if not validated_payload.get("item_norm"):
                validated_payload["item_norm"] = validated_payload["item_name"].lower().replace(" ", "_")

        elif etype == EventType.ACTION_TAKEN:
            parsed_act = ActionTakenSchema.model_validate(payload)
            validated_payload = parsed_act.model_dump()
            try:
                validated_payload["kind"] = ActionKind(validated_payload["kind"].lower())
            except ValueError:
                validated_payload["kind"] = ActionKind.COORDINATION

        elif etype == EventType.NOTE_RECORDED:
            parsed_note = NoteRecordedSchema.model_validate(payload)
            validated_payload = parsed_note.model_dump()

        else:
            validated_payload = dict(payload)

    except ValidationError as ve:
        raise ExtractionValidationError(f"Schema validation failed for {etype.value}: {ve}") from ve

    # 3. Validate member IDs if present (NEVER silently replace)
    for member_field in ("member_id", "paid_by", "reported_by", "restocked_by", "tracked_by"):
        mid = validated_payload.get(member_field)
        if mid is not None:
            mid_str = str(mid)
            if valid_member_ids and mid_str not in valid_member_ids:
                raise ExtractionValidationError(
                    f"Member '{mid_str}' in field '{member_field}' is not a registered house member."
                )

    if validated_payload.get("participant_ids"):
        pids = validated_payload["participant_ids"]
        for p in pids:
            if valid_member_ids and p not in valid_member_ids:
                raise ExtractionValidationError(
                    f"Participant '{p}' is not a registered house member."
                )
        validated_payload["participant_ids"] = tuple(pids)

    return etype, validated_payload
