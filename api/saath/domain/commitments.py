"""Commitment state machine, derived overdue calculation, and reply resolution engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Sequence

from saath.domain.events import CommitmentState


class CommitmentDomainError(Exception):
    """Base exception for commitment domain logic."""


class TerminalStateError(CommitmentDomainError):
    """Raised when an action is attempted on a completed or cancelled commitment."""


class InvalidStateTransitionError(CommitmentDomainError):
    """Raised when an invalid state transition is requested."""


@dataclass(frozen=True, slots=True)
class Commitment:
    id: str
    house_id: str
    title: str
    promise_made_by: str
    responsible_party: str
    tracked_by: str
    state: CommitmentState = CommitmentState.WAITING
    due_at: int | None = None  # UTC epoch milliseconds, None if no explicit due date
    issue_id: str | None = None
    source_event_id: str | None = None
    snoozed_until: int | None = None
    created_at: int = 0
    updated_at: int = 0

    def is_overdue(self, now_ms: int) -> bool:
        """
        Overdue is strictly derived.
        Never stored: state == waiting AND due_at is not None AND due_at < now_ms.
        """
        if self.state != CommitmentState.WAITING or self.due_at is None:
            return False
        return self.due_at < now_ms

    def is_snoozed(self, now_ms: int) -> bool:
        """Returns True if commitment is actively snoozed."""
        return self.snoozed_until is not None and self.snoozed_until > now_ms

    def needs_attention(self, now_ms: int) -> bool:
        """
        Returns True if commitment requires active user attention:
        waiting, overdue, and not actively snoozed.
        """
        return self.is_overdue(now_ms) and not self.is_snoozed(now_ms)

    def is_terminal(self) -> bool:
        """Returns True if commitment is in a terminal state (done or cancelled)."""
        return self.state in (CommitmentState.DONE, CommitmentState.CANCELLED)


def transition_commitment(
    commitment: Commitment,
    target_state: CommitmentState,
    new_due_at: int | None = None,
    now_ms: int = 0,
) -> Commitment:
    """
    Applies pure state transition rules.
    Terminal states (DONE, CANCELLED) cannot be transitioned.
    """
    if commitment.is_terminal():
        raise TerminalStateError(
            f"Commitment '{commitment.id}' is in terminal state '{commitment.state.value}' "
            "and cannot be modified."
        )

    if target_state == CommitmentState.RESCHEDULED:
        if new_due_at is None:
            raise InvalidStateTransitionError(
                "Rescheduled commitment requires a new_due_at timestamp."
            )
        if now_ms > 0 and new_due_at <= now_ms:
            raise InvalidStateTransitionError(
                f"New due date ({new_due_at}) must be in the future (after {now_ms})."
            )
        # When rescheduled, it resets to waiting semantics with the new due_at
        return Commitment(
            id=commitment.id,
            house_id=commitment.house_id,
            title=commitment.title,
            promise_made_by=commitment.promise_made_by,
            responsible_party=commitment.responsible_party,
            tracked_by=commitment.tracked_by,
            due_at=new_due_at,
            state=CommitmentState.WAITING,
            issue_id=commitment.issue_id,
            source_event_id=commitment.source_event_id,
            snoozed_until=None,
            created_at=commitment.created_at,
            updated_at=now_ms,
        )

    return Commitment(
        id=commitment.id,
        house_id=commitment.house_id,
        title=commitment.title,
        promise_made_by=commitment.promise_made_by,
        responsible_party=commitment.responsible_party,
        tracked_by=commitment.tracked_by,
        due_at=commitment.due_at,
        state=target_state,
        issue_id=commitment.issue_id,
        source_event_id=commitment.source_event_id,
        snoozed_until=commitment.snoozed_until,
        created_at=commitment.created_at,
        updated_at=now_ms,
    )


class ReplyIntent(str, Enum):
    NOT_YET = "not_yet"
    RESCHEDULED = "rescheduled"
    DONE = "done"
    CANCELLED = "cancelled"
    SOMEONE_ELSE_DID = "someone_else_did"
    ASK_WHICH = "ask_which"
    UNRELATED = "unrelated"


@dataclass(frozen=True, slots=True)
class TargetCandidate:
    commitment_id: str
    title: str
    score: float


@dataclass(frozen=True, slots=True)
class ReplyResolutionResult:
    intent: ReplyIntent
    target_commitment: Commitment | None = None
    new_due_at: int | None = None
    acting_member: str | None = None
    ask_which_candidates: tuple[TargetCandidate, ...] = ()
    confidence: float = 1.0


# Common multilingual short reply regex patterns
NOT_YET_PATTERNS = [r"\b(nahi|nahi hua|abhi tak nahi|abhi nahi|not yet|still pending|pending)\b"]
DONE_PATTERNS = [
    r"\b(aa gaya|ho gaya|done|hogaya|fixed|complete|completed|theek ho gaya|kar diya|khatam)\b"
]
CANCELLED_PATTERNS = [r"\b(chhod do|chhod de|cancel|cancelled|mat karo|rehne do|drop)\b"]
RESCHEDULED_PATTERNS = [
    r"\b(kal aayega|parso aayega|kal aayenge|parso|kal|reschedule|delayed|next week|aaj shaam)\b"
]


def classify_reply_intent(text: str) -> tuple[ReplyIntent, str | None]:
    """Classifies short-reply intent using rule heuristics, returning intent and potential actor."""
    t = text.lower().strip()

    # If it is a full statement with reporting/promise verbs, it is a new report, NOT a short reply
    if any(k in t for k in ["bhejega", "bola", "promised", "leak", "kharab", "bill", "khatam", "paid"]):
        return ReplyIntent.UNRELATED, None

    # Check "X ne kar diya" or "X did it" on original text to preserve proper casing
    pattern = r"\b(\w+)\s+(?:ne kar diya|ne kiya|did it|handled it)\b"
    m_someone = re.search(pattern, text.strip(), re.IGNORECASE)
    if m_someone:
        member_name = m_someone.group(1)
        return ReplyIntent.SOMEONE_ELSE_DID, member_name

    for pat in DONE_PATTERNS:
        if re.search(pat, t):
            return ReplyIntent.DONE, None

    for pat in CANCELLED_PATTERNS:
        if re.search(pat, t):
            return ReplyIntent.CANCELLED, None

    for pat in RESCHEDULED_PATTERNS:
        if re.search(pat, t):
            return ReplyIntent.RESCHEDULED, None

    for pat in NOT_YET_PATTERNS:
        if re.search(pat, t):
            return ReplyIntent.NOT_YET, None

    return ReplyIntent.UNRELATED, None


def score_commitment_match(text: str, commitment: Commitment) -> float:
    """Scores a commitment candidate against reply text using token overlap."""
    text_tokens = set(re.findall(r"\w+", text.lower()))
    target_str = f"{commitment.title} {commitment.responsible_party} {commitment.promise_made_by}"
    target_tokens = set(re.findall(r"\w+", target_str.lower()))
    if not text_tokens or not target_tokens:
        return 0.0
    overlap = text_tokens.intersection(target_tokens)
    return len(overlap) / max(1, len(text_tokens))


def resolve_reply(
    text: str,
    open_commitments: Sequence[Commitment],
    now_ms: int,
    house_tz_str: str = "Asia/Kolkata",
    time_resolver_func: Callable[[str, int, str], int] | None = None,
) -> ReplyResolutionResult:
    """
    Resolves a short reply against open commitments.

    Target selection:
    1. If explicit entity/title tokens match a specific commitment with clear margin -> select it.
    2. Else if only a single open commitment exists -> select it.
    3. Else if ambiguous candidates exist -> return AskWhich (max 3 candidates).
    4. Else return Unrelated.
    """
    if not open_commitments:
        return ReplyResolutionResult(intent=ReplyIntent.UNRELATED)

    intent, acting_member = classify_reply_intent(text)
    if intent == ReplyIntent.UNRELATED:
        return ReplyResolutionResult(intent=ReplyIntent.UNRELATED)

    # Resolve new due_at if rescheduled
    new_due_at = None
    if intent == ReplyIntent.RESCHEDULED:
        new_due_at = (
            time_resolver_func(text, now_ms, house_tz_str)
            if time_resolver_func
            else now_ms + (24 * 3600 * 1000)
        )

    # If only 1 open commitment, it's unambiguous
    if len(open_commitments) == 1:
        return ReplyResolutionResult(
            intent=intent,
            target_commitment=open_commitments[0],
            new_due_at=new_due_at,
            acting_member=acting_member,
            confidence=0.95,
        )

    # Score all open commitments by token overlap
    scored: list[tuple[float, Commitment]] = []
    for c in open_commitments:
        score = score_commitment_match(text, c)
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_score, top_c = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    # If top score is clearly distinct (margin threshold >= 0.2 and score > 0)
    if top_score > 0.0 and (top_score - second_score >= 0.2):
        return ReplyResolutionResult(
            intent=intent,
            target_commitment=top_c,
            new_due_at=new_due_at,
            acting_member=acting_member,
            confidence=0.85,
        )

    # If top candidates have close scores or zero explicit token overlap, prompt AskWhich
    candidates = tuple(
        TargetCandidate(commitment_id=c.id, title=c.title, score=score) for score, c in scored[:3]
    )
    return ReplyResolutionResult(
        intent=ReplyIntent.ASK_WHICH,
        target_commitment=None,
        new_due_at=new_due_at,
        acting_member=acting_member,
        ask_which_candidates=candidates,
        confidence=0.5,
    )


@dataclass(frozen=True, slots=True)
class NextAction:
    label: str
    kind: str
    payload: dict[str, str | int]


def derive_next_action(
    item_type: str,
    item_data: dict[str, str | int],
    is_overdue: bool = False,
) -> NextAction | None:
    """
    Pure next action engine mapping (item_type, state) -> NextAction.
    """
    if item_type == "commitment":
        state = str(item_data.get("state", "waiting"))
        responsible = str(item_data.get("responsible_party", "someone"))
        if is_overdue or state == "overdue":
            return NextAction(
                label=f"Follow up with {responsible}",
                kind="followup",
                payload={"commitment_id": item_data.get("id", ""), "responsible": responsible},
            )
        elif state == "waiting":
            return NextAction(
                label=f"Waiting on {responsible}",
                kind="waiting",
                payload={"commitment_id": item_data.get("id", ""), "responsible": responsible},
            )

    elif item_type == "supply":
        status = str(item_data.get("status", "available"))
        item_name = str(item_data.get("item_name", "item"))
        if status == "depleted":
            return NextAction(
                label=f"Ask someone to restock {item_name}",
                kind="restock",
                payload={"item_name": item_name},
            )

    elif item_type == "expense":
        is_confirmed = bool(item_data.get("is_confirmed", False))
        if not is_confirmed:
            return NextAction(
                label="Confirm expense split",
                kind="confirm_expense",
                payload={"expense_id": item_data.get("id", "")},
            )
        else:
            return NextAction(
                label="Expense split recorded",
                kind="info",
                payload={"expense_id": item_data.get("id", "")},
            )

    return None
