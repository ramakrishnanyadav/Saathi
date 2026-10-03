"""Port protocol for commitment slip risk and supply run-out forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class SlipRisk:
    commitment_id: str
    probability_slip: float  # 0.0 to 1.0
    risk_level: str  # "low", "medium", "high"
    explanation: str
    is_estimate: bool = True
    has_enough_history: bool = True


@dataclass(frozen=True, slots=True)
class RunoutEstimate:
    item_norm: str
    item_name: str
    estimated_days_remaining: float
    probability_depleted_soon: float
    explanation: str
    is_estimate: bool = True
    has_enough_history: bool = True


class Forecaster(Protocol):
    """Protocol for forecasting commitment slip risk and supply runout timelines."""

    def predict_slip(
        self,
        commitment_features: dict[str, Any],
        historical_commitments: Sequence[dict[str, Any]],
    ) -> SlipRisk:
        """Predicts slip risk for an open commitment based on past vendor follow-through."""
        ...

    def predict_runout(
        self,
        item_norm: str,
        item_name: str,
        restock_history_days: Sequence[float],
    ) -> RunoutEstimate:
        """Predicts remaining days until supply runout based on historical restock intervals."""
        ...
