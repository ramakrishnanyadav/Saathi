"""Money math strictly in paise with Hare-Niemeyer largest-remainder split."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

MIN_PAISE = 1
MAX_PAISE = 10_000_000  # ₹100,000.00


class MoneyError(Exception):
    """Base exception for money domain operations."""


class InvalidAmountError(MoneyError):
    """Raised when an amount is outside acceptable bounds or not an integer."""


class InvalidParticipantError(MoneyError):
    """Raised when participants sequence is empty or invalid."""


@dataclass(frozen=True, slots=True)
class SplitResult:
    total_paise: int
    shares: dict[str, int]


def validate_paise_amount(amount_paise: int) -> None:
    """Validate that amount_paise is an integer strictly within valid bounds."""
    if not isinstance(amount_paise, int) or isinstance(amount_paise, bool):
        raise InvalidAmountError(f"Amount must be an integer, got {type(amount_paise).__name__}")
    if amount_paise < MIN_PAISE or amount_paise > MAX_PAISE:
        raise InvalidAmountError(
            f"Amount {amount_paise} paise out of bounds [{MIN_PAISE}, {MAX_PAISE}]"
        )


def split_equally(total_paise: int, participant_ids: Sequence[str]) -> SplitResult:
    """
    Splits total_paise among participants using the Hare-Niemeyer (largest-remainder) method.

    Guarantees:
      1. Every participant receives an integer number of paise.
      2. Sum of all shares equals total_paise exactly.
      3. Difference between any two shares is at most 1 paisa.
      4. Deterministic assignment of extra remainder paise (sorted by participant_id).

    Complexity: O(n log n) where n is participant count (due to sorting for determinism).
    """
    validate_paise_amount(total_paise)

    if not participant_ids:
        raise InvalidParticipantError("Participants list cannot be empty.")

    # Deduplicate while preserving unique participants, sort for stable determinism
    unique_participants = sorted(set(participant_ids))
    n = len(unique_participants)
    if n == 0:
        raise InvalidParticipantError("No unique participants provided.")

    base_share = total_paise // n
    remainder = total_paise % n

    shares: dict[str, int] = {}
    for idx, pid in enumerate(unique_participants):
        extra = 1 if idx < remainder else 0
        shares[pid] = base_share + extra

    # Invariant assertion
    assert sum(shares.values()) == total_paise, "Hare-Niemeyer invariant violated"
    return SplitResult(total_paise=total_paise, shares=shares)


def format_rupees(paise: int, include_symbol: bool = True) -> str:
    """
    Formats paise into an Indian Rupee string without floating point conversion.
    e.g. 145000 paise -> "₹1,450.00", 48333 paise -> "₹483.33", -500 paise -> "-₹5.00"
    """
    if not isinstance(paise, int) or isinstance(paise, bool):
        raise InvalidAmountError("Paise must be an integer.")

    is_negative = paise < 0
    abs_paise = abs(paise)
    rupees = abs_paise // 100
    rem_paise = abs_paise % 100

    # Indian number formatting for rupee portion
    s = str(rupees)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        # Group in pairs of 2 from right
        chunks: list[str] = []
        while len(rest) > 2:
            chunks.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            chunks.insert(0, rest)
        rupees_formatted = ",".join(chunks) + "," + last3
    else:
        rupees_formatted = s

    result = f"{rupees_formatted}.{rem_paise:02d}"
    prefix = "-" if is_negative else ""
    sym = "₹" if include_symbol else ""
    return f"{prefix}{sym}{result}"
