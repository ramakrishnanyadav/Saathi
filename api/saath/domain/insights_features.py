"""Pure feature extraction functions for commitment slip and supply depletion forecasting."""

from __future__ import annotations

from typing import Any, Sequence


def extract_commitment_features(
    commitment: dict[str, Any],
    historical_commitments: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """
    Extracts pure tabular features for a commitment from vendor history:
    - vendor_name
    - promised_delay_hours
    - reschedule_count
    - prior_commitments_for_vendor
    - prior_slips_for_vendor
    - vendor_on_time_rate
    """
    vendor = str(commitment.get("responsible_party", "vendor")).strip().lower()
    due_at = commitment.get("due_at")
    created_at = commitment.get("created_at", 0)

    promised_delay_hours = (
        (due_at - created_at) / 3600000.0 if (due_at and created_at and due_at > created_at) else 24.0
    )

    vendor_history = [
        c for c in historical_commitments
        if str(c.get("responsible_party", "")).strip().lower() == vendor and c.get("state") in ("done", "rescheduled", "cancelled")
    ]

    prior_count = len(vendor_history)
    prior_slips = sum(
        1 for c in vendor_history if c.get("state") in ("rescheduled", "cancelled") or (c.get("updated_at", 0) > c.get("due_at", 0) > 0)
    )

    on_time_rate = (prior_count - prior_slips) / prior_count if prior_count > 0 else 1.0

    return {
        "commitment_id": commitment.get("id"),
        "vendor_name": vendor,
        "promised_delay_hours": promised_delay_hours,
        "reschedule_count": commitment.get("reschedule_count", 0),
        "prior_commitments_for_vendor": prior_count,
        "prior_slips_for_vendor": prior_slips,
        "vendor_on_time_rate": on_time_rate,
    }


def extract_supply_interval_features(
    restock_timestamps_ms: Sequence[int],
) -> list[float]:
    """Converts a sequence of restock timestamps into interval days between restocks."""
    if len(restock_timestamps_ms) < 2:
        return []

    sorted_ts = sorted(restock_timestamps_ms)
    intervals: list[float] = []
    for i in range(1, len(sorted_ts)):
        diff_days = (sorted_ts[i] - sorted_ts[i - 1]) / 86400000.0
        if diff_days > 0.1:
            intervals.append(diff_days)
    return intervals
