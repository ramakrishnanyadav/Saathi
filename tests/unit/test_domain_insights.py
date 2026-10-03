"""Unit tests for weekly reflection aggregation of invisible and coordination work."""

from datetime import datetime
from zoneinfo import ZoneInfo

from saath.domain.events import ActionKind
from saath.domain.insights import ActionRecord, aggregate_weekly_reflection, get_week_bounds


def test_weekly_aggregation_across_bounds():
    """Actions are aggregated strictly within the week window; counts match by type."""
    tz = ZoneInfo("Asia/Kolkata")
    
    # Monday Oct 5, 2026, 12:00
    mid_week_dt = datetime(2026, 10, 5, 12, 0, tzinfo=tz)
    mid_week_ms = int(mid_week_dt.timestamp() * 1000)

    week_start, week_end = get_week_bounds(mid_week_ms, "Asia/Kolkata")

    # Member names
    names = {"m-1": "Pooja", "m-2": "Rahul"}

    # Actions: 3 within the week, 1 before week, 1 after week
    actions = [
        # Before week
        ActionRecord(member_id="m-1", kind=ActionKind.PHYSICAL, label="Took out trash", occurred_at=week_start - 1000),
        # Within week
        ActionRecord(member_id="m-1", kind=ActionKind.COORDINATION, label="Called landlord", occurred_at=week_start + 1000),
        ActionRecord(member_id="m-1", kind=ActionKind.COORDINATION, label="Followed up with plumber", occurred_at=week_start + 2000),
        ActionRecord(member_id="m-1", kind=ActionKind.COORDINATION, label="Followed up with plumber", occurred_at=week_start + 3000),
        ActionRecord(member_id="m-2", kind=ActionKind.PHYSICAL, label="Bought groceries", occurred_at=week_start + 4000),
        # After week
        ActionRecord(member_id="m-2", kind=ActionKind.PHYSICAL, label="Cleaned hall", occurred_at=week_end + 1000),
    ]

    reflection = aggregate_weekly_reflection(actions, names, week_start, week_end)

    # Asserts for member 1 (Pooja)
    pooja_summary = reflection.summaries["m-1"]
    assert pooja_summary.physical_count == 0
    assert pooja_summary.coordination_count == 3
    assert pooja_summary.breakdown_by_label["Followed up with plumber"] == 2
    assert pooja_summary.breakdown_by_label["Called landlord"] == 1

    # Asserts for member 2 (Rahul)
    rahul_summary = reflection.summaries["m-2"]
    assert rahul_summary.physical_count == 1
    assert rahul_summary.coordination_count == 0

    # Neutral rebalance suggestion offered
    assert reflection.rebalance_suggestion is not None
    assert "Coordination work was concentrated on one person" in reflection.rebalance_suggestion
