"""Unit tests for assignee suggestion heuristic."""

from saath.domain.suggestions import MemberWorkload, suggest_assignee


def test_least_recent_handler_wins():
    """Member who handled least recently or never handled wins."""
    m1 = MemberWorkload(
        member_id="m-1",
        name="Amit",
        open_commitments_count=1,
        last_handled_time_ms=None,  # Never handled
        recent_actions_count=2,
    )
    m2 = MemberWorkload(
        member_id="m-2",
        name="Rohan",
        open_commitments_count=1,
        last_handled_time_ms=1_000_000,
        recent_actions_count=5,
    )
    m3 = MemberWorkload(
        member_id="m-3",
        name="Pooja",
        open_commitments_count=1,
        last_handled_time_ms=500_000,  # Handled earlier than Rohan
        recent_actions_count=3,
    )

    # Amit has never handled, so Amit should win
    suggestion = suggest_assignee("groceries", [m1, m2, m3])
    assert suggestion is not None
    assert suggestion.member_id == "m-1"
    assert "Amit hasn't handled groceries yet" in suggestion.reason


def test_overloaded_member_bypassed():
    """Overloaded members (>5 open) are bypassed unless all are overloaded."""
    m1 = MemberWorkload(
        member_id="m-1",
        name="Amit",
        open_commitments_count=6,  # Overloaded!
        last_handled_time_ms=None,
        recent_actions_count=1,
    )
    m2 = MemberWorkload(
        member_id="m-2",
        name="Rohan",
        open_commitments_count=2,  # Not overloaded
        last_handled_time_ms=100_000,
        recent_actions_count=2,
    )

    suggestion = suggest_assignee("restock", [m1, m2])
    assert suggestion is not None
    assert suggestion.member_id == "m-2"


def test_single_member_household():
    """Works gracefully with 1 member household."""
    m1 = MemberWorkload(
        member_id="m-1",
        name="SoleResident",
        open_commitments_count=0,
        last_handled_time_ms=50_000,
        recent_actions_count=1,
    )
    suggestion = suggest_assignee("trash", [m1])
    assert suggestion is not None
    assert suggestion.member_id == "m-1"
    assert suggestion.name == "SoleResident"


def test_kind_specific_history_wins():
    """Member who specifically hasn't handled the requested kind wins over generic history."""
    m1 = MemberWorkload(
        member_id="m-1",
        name="Amit",
        open_commitments_count=1,
        last_handled_time_ms=100,
        last_handled_by_kind={"plumber": 500_000, "groceries": 100},
    )
    m2 = MemberWorkload(
        member_id="m-2",
        name="Rohan",
        open_commitments_count=1,
        last_handled_time_ms=200,
        last_handled_by_kind={"plumber": 100_000, "groceries": 800_000},
    )

    # For plumber: Rohan handled at 100,000, Amit at 500,000 -> Rohan handled least recently!
    sug = suggest_assignee("plumber", [m1, m2])
    assert sug is not None
    assert sug.member_id == "m-2"
    assert "Rohan hasn't handled plumber recently" in sug.reason
