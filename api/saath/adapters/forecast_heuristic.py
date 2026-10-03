"""Heuristic adapter for commitment slip risk and supply run-out forecasting."""

from __future__ import annotations

import statistics
from typing import Any, Sequence

from saath.ports.forecast import RunoutEstimate, SlipRisk


class HeuristicForecaster:
    """
    Always available zero-dependency forecaster using smoothed per-vendor slip rates
    and median restock intervals.
    Never profiles or targets flatmates — vendor, supply, and expense categories only.
    """

    def predict_slip(
        self,
        commitment_features: dict[str, Any],
        historical_commitments: Sequence[dict[str, Any]],
    ) -> SlipRisk:
        cid = str(commitment_features.get("commitment_id", ""))
        vendor = str(commitment_features.get("vendor_name", "vendor")).title()
        prior_count = int(commitment_features.get("prior_commitments_for_vendor", 0))

        if prior_count < 2:
            return SlipRisk(
                commitment_id=cid,
                probability_slip=0.25,
                risk_level="low",
                explanation=f"Not enough history yet for {vendor} (fewer than 2 past visits recorded).",
                is_estimate=True,
                has_enough_history=False,
            )

        prior_slips = int(commitment_features.get("prior_slips_for_vendor", 0))
        # Laplace smoothing: (slips + 1) / (total + 2)
        prob_slip = (prior_slips + 1.0) / (prior_count + 2.0)
        on_time_count = prior_count - prior_slips

        if prob_slip >= 0.55:
            level = "high"
        elif prob_slip >= 0.30:
            level = "medium"
        else:
            level = "low"

        explanation = (
            f"Estimated slip risk for {vendor}: arrived on time {on_time_count} of {prior_count} times in past visits."
        )

        return SlipRisk(
            commitment_id=cid,
            probability_slip=round(prob_slip, 2),
            risk_level=level,
            explanation=explanation,
            is_estimate=True,
            has_enough_history=True,
        )

    def predict_runout(
        self,
        item_norm: str,
        item_name: str,
        restock_history_days: Sequence[float],
    ) -> RunoutEstimate:
        if len(restock_history_days) < 2:
            return RunoutEstimate(
                item_norm=item_norm,
                item_name=item_name,
                estimated_days_remaining=7.0,
                probability_depleted_soon=0.2,
                explanation=f"Not enough restock history yet for {item_name}.",
                is_estimate=True,
                has_enough_history=False,
            )

        median_interval = statistics.median(restock_history_days)
        last_interval = restock_history_days[-1]
        days_remaining = max(0.5, median_interval - last_interval)

        prob_depleted = 0.8 if days_remaining <= 3.0 else (0.4 if days_remaining <= 5.0 else 0.1)

        explanation = f"Estimated {item_name} runout in ~{days_remaining:.1f} days based on median restock interval of {median_interval:.1f} days."

        return RunoutEstimate(
            item_norm=item_norm,
            item_name=item_name,
            estimated_days_remaining=round(days_remaining, 1),
            probability_depleted_soon=prob_depleted,
            explanation=explanation,
            is_estimate=True,
            has_enough_history=True,
        )
