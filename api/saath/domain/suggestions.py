"""Assignee suggestion heuristics based on workload and rotation history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class MemberWorkload:
    member_id: str
    name: str
    open_commitments_count: int
    last_handled_time_ms: int | None = None  # None means never handled
    recent_actions_count: int = 0
    last_handled_by_kind: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AssigneeSuggestion:
    member_id: str
    name: str
    reason: str


def suggest_assignee(
    item_kind: str,
    members: Sequence[MemberWorkload],
    max_open_threshold: int = 5,
) -> AssigneeSuggestion | None:
    """
    Selects a member to suggest for an action/commitment based on:
    1. Filter out members overloaded with open tracked commitments (> max_open_threshold).
       (If all are overloaded, consider all).
    2. Prefer the candidate who handled this item_kind least recently
       (using last_handled_by_kind[item_kind] if available, otherwise last_handled_time_ms).
    3. Tie-break by fewest recent actions, then deterministically by member_id.

    Returns a neutral, honest suggestion with an explanatory rationale.
    Complexity: O(m log m) where m is member count (typically 2-6 flatmates).
    """
    if not members:
        return None

    # Step 1: Workload filter
    eligible = [m for m in members if m.open_commitments_count < max_open_threshold]
    if not eligible:
        eligible = list(members)

    # Step 2: Sorting key: (never_handled, handled_time, recent_actions, member_id)
    def sort_key(m: MemberWorkload) -> tuple[int, int, int, str]:
        t = m.last_handled_by_kind.get(item_kind, m.last_handled_time_ms)
        never_handled = 0 if t is None else 1
        handled_time = -1 if t is None else t
        return (never_handled, handled_time, m.recent_actions_count, m.member_id)

    eligible.sort(key=sort_key)
    chosen = eligible[0]

    chosen_time = chosen.last_handled_by_kind.get(item_kind, chosen.last_handled_time_ms)
    # Generate calm, neutral reason
    if chosen_time is None:
        reason = f"{chosen.name} hasn't handled {item_kind} yet"
    else:
        reason = f"{chosen.name} hasn't handled {item_kind} recently"

    return AssigneeSuggestion(
        member_id=chosen.member_id,
        name=chosen.name,
        reason=reason,
    )
