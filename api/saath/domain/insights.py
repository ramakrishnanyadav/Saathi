"""Weekly reflection aggregation of invisible and coordination work without scores or rankings."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Sequence
from zoneinfo import ZoneInfo

from saath.domain.events import ActionKind


@dataclass(frozen=True, slots=True)
class ActionRecord:
    member_id: str
    kind: ActionKind
    label: str
    occurred_at: int  # UTC epoch ms


@dataclass(frozen=True, slots=True)
class MemberWeeklySummary:
    member_id: str
    member_name: str
    physical_count: int
    coordination_count: int
    breakdown_by_label: dict[str, int]


@dataclass(frozen=True, slots=True)
class WeeklyReflection:
    week_start_ms: int
    week_end_ms: int
    summaries: dict[str, MemberWeeklySummary]
    rebalance_suggestion: str | None = None


def get_week_bounds(timestamp_ms: int, house_tz_str: str = "Asia/Kolkata") -> tuple[int, int]:
    """
    Returns (week_start_ms, week_end_ms) for the week containing timestamp_ms.
    Week starts on Monday 00:00:00.000 in house local time.
    """
    try:
        tz = ZoneInfo(house_tz_str)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=tz)
    # Start of Monday
    days_since_monday = dt.weekday()
    monday_date = dt.date() - timedelta(days=days_since_monday)
    start_dt = datetime.combine(monday_date, time(0, 0, 0), tzinfo=tz)
    end_dt = start_dt + timedelta(days=7)

    return int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)


def aggregate_weekly_reflection(
    actions: Sequence[ActionRecord],
    member_names: dict[str, str],
    week_start_ms: int,
    week_end_ms: int,
) -> WeeklyReflection:
    """
    Aggregates actions strictly within [week_start_ms, week_end_ms).

    Principles:
      1. No global totals.
      2. No ranking or sorting by score or action count.
      3. Preserves stable order of members (by member_id).

    Complexity: O(E_week) where E_week is action count in that week.
    """
    member_physical: dict[str, int] = defaultdict(int)
    member_coord: dict[str, int] = defaultdict(int)
    member_labels: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for a in actions:
        if week_start_ms <= a.occurred_at < week_end_ms:
            if a.kind == ActionKind.PHYSICAL:
                member_physical[a.member_id] += 1
            elif a.kind == ActionKind.COORDINATION:
                member_coord[a.member_id] += 1
            member_labels[a.member_id][a.label] += 1

    summaries: dict[str, MemberWeeklySummary] = {}
    for mid in sorted(member_names.keys()):
        summaries[mid] = MemberWeeklySummary(
            member_id=mid,
            member_name=member_names[mid],
            physical_count=member_physical[mid],
            coordination_count=member_coord[mid],
            breakdown_by_label=dict(member_labels[mid]),
        )

    # Calm, non-judgmental observation without identifying, scoring, or ranking members
    rebalance_note = None
    coord_counts = [s.coordination_count for s in summaries.values()]
    if coord_counts and max(coord_counts) >= 3 and min(coord_counts) == 0:
        rebalance_note = (
            "Coordination work was concentrated on one person this week. "
            "Consider swapping coordination tasks next week."
        )

    return WeeklyReflection(
        week_start_ms=week_start_ms,
        week_end_ms=week_end_ms,
        summaries=summaries,
        rebalance_suggestion=rebalance_note,
    )
