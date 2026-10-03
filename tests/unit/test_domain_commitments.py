"""Unit tests for commitment domain state machine and overdue logic."""

import pytest
from saath.domain.commitments import (
    Commitment,
    CommitmentState,
    ReplyIntent,
    TerminalStateError,
    derive_next_action,
    resolve_reply,
    transition_commitment,
)


def make_test_commitment(
    id: str = "c-1",
    state: CommitmentState = CommitmentState.WAITING,
    due_at: int = 1_000_000,
    snoozed_until: int | None = None,
    title: str = "Fix bathroom tap",
    responsible_party: str = "Landlord",
    tracked_by: str = "m-1",
) -> Commitment:
    return Commitment(
        id=id,
        house_id="h-1",
        title=title,
        promise_made_by="Landlord",
        responsible_party=responsible_party,
        tracked_by=tracked_by,
        due_at=due_at,
        state=state,
        snoozed_until=snoozed_until,
    )


def test_waiting_to_overdue_boundary():
    """Test 1: Waiting -> overdue exactly at due_at boundary (-1 ms, 0, +1 ms)."""
    due_at = 1_000_000
    c = make_test_commitment(due_at=due_at)

    # 1 ms before due_at: not overdue
    assert not c.is_overdue(now_ms=due_at - 1)
    # Exactly at due_at: due_at is not strictly < now_ms
    assert not c.is_overdue(now_ms=due_at)
    # 1 ms after due_at: overdue!
    assert c.is_overdue(now_ms=due_at + 1)


def test_overdue_is_derived_no_stored_mutation():
    """Test 2: Overdue is derived; no stored mutation when time advances."""
    c = make_test_commitment(due_at=1_000_000)
    assert c.state == CommitmentState.WAITING

    # Advance time arbitrarily
    assert not c.is_overdue(now_ms=500_000)
    assert c.is_overdue(now_ms=2_000_000)
    # Commitment object is immutable and state remains WAITING
    assert c.state == CommitmentState.WAITING


def test_rescheduled_new_due_and_overdue_again():
    """Test 3: Rescheduled -> new due -> overdue again later."""
    c = make_test_commitment(due_at=1_000_000)
    assert c.is_overdue(now_ms=1_000_500)

    # Reschedule to a future time
    c_rescheduled = transition_commitment(
        c,
        target_state=CommitmentState.RESCHEDULED,
        new_due_at=2_000_000,
        now_ms=1_000_500,
    )
    # Rescheduled commitment behaves as waiting with new due_at
    assert c_rescheduled.state == CommitmentState.WAITING
    assert c_rescheduled.due_at == 2_000_000
    assert not c_rescheduled.is_overdue(now_ms=1_500_000)
    # Once time passes 2_000_000, it is overdue again
    assert c_rescheduled.is_overdue(now_ms=2_000_001)


def test_terminal_states_raise_typed_error():
    """Test 4: done/cancelled are terminal; late update returns typed error."""
    c = make_test_commitment()
    c_done = transition_commitment(c, target_state=CommitmentState.DONE, now_ms=100)
    assert c_done.state == CommitmentState.DONE
    assert c_done.is_terminal()

    with pytest.raises(TerminalStateError):
        transition_commitment(c_done, target_state=CommitmentState.WAITING, now_ms=200)

    c_cancelled = transition_commitment(c, target_state=CommitmentState.CANCELLED, now_ms=100)
    assert c_cancelled.state == CommitmentState.CANCELLED
    with pytest.raises(TerminalStateError):
        transition_commitment(c_cancelled, target_state=CommitmentState.DONE, now_ms=200)


def test_snooze_suppresses_alerting():
    """Test 5: Snooze suppresses nudge until snoozed_until via needs_attention."""
    c = make_test_commitment(due_at=1_000_000, snoozed_until=1_500_000)
    # The item is technically overdue by due_at, but is actively snoozed
    assert c.is_overdue(now_ms=1_200_000)
    assert c.is_snoozed(now_ms=1_200_000)
    # Crucial semantic: needs_attention is FALSE while snoozed!
    assert not c.needs_attention(now_ms=1_200_000)

    # After snoozed_until has passed:
    assert not c.is_snoozed(now_ms=1_600_000)
    assert c.needs_attention(now_ms=1_600_000)


def test_reschedule_must_be_in_future():
    """Rescheduling to a past or current timestamp raises InvalidStateTransitionError."""
    from saath.domain.commitments import InvalidStateTransitionError
    c = make_test_commitment(due_at=1_000_000)
    with pytest.raises(InvalidStateTransitionError):
        transition_commitment(
            c,
            target_state=CommitmentState.RESCHEDULED,
            new_due_at=500_000,  # in the past!
            now_ms=1_000_500,
        )


def test_reply_resolution_scenarios():
    """Test 6: Reply resolution: single open item auto-targets; close candidates -> AskWhich; explicit mention wins."""
    c1 = make_test_commitment(id="c-1", title="Plumber repair")
    
    # 6a. Single open item auto-targets
    res1 = resolve_reply("nahi", [c1], now_ms=100)
    assert res1.intent == ReplyIntent.NOT_YET
    assert res1.target_commitment == c1

    # 6b. Explicit mention wins over multiple candidates
    c2 = make_test_commitment(id="c-2", title="Electrician fuse fix", responsible_party="Sharma Electrician")
    res2 = resolve_reply("electrician aa gaya", [c1, c2], now_ms=100)
    assert res2.intent == ReplyIntent.DONE
    assert res2.target_commitment == c2

    # 6c. Ambiguous reply with multiple items -> AskWhich (NEVER auto-resolve!)
    res3 = resolve_reply("ho gaya", [c1, c2], now_ms=100)
    assert res3.intent == ReplyIntent.ASK_WHICH  # Must never auto-guess when ambiguous
    assert res3.target_commitment is None
    assert len(res3.ask_which_candidates) >= 2


def test_someone_else_did_credits_member():
    """Test 7: 'someone else did it' credits named member."""
    c1 = make_test_commitment(id="c-1", title="Order cooking gas")
    res = resolve_reply("Rahul ne kar diya", [c1], now_ms=100)
    assert res.intent == ReplyIntent.SOMEONE_ELSE_DID
    assert res.acting_member == "Rahul"
    assert res.target_commitment == c1


def test_next_action_derivation():
    """Test next action derivation for overdue, waiting, and supply items."""
    na_overdue = derive_next_action("commitment", {"id": "c-1", "responsible_party": "Landlord"}, is_overdue=True)
    assert na_overdue is not None
    assert na_overdue.label == "Follow up with Landlord"
    assert na_overdue.kind == "followup"

    na_supply = derive_next_action("supply", {"item_name": "milk", "status": "depleted"})
    assert na_supply is not None
    assert na_supply.label == "Ask someone to restock milk"
    assert na_supply.kind == "restock"
