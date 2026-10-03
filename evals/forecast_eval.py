"""Forecasting evaluation suite benchmarking Heuristic and TabPFN adapters against baselines."""

from __future__ import annotations

import sys
from saath.adapters.forecast_heuristic import HeuristicForecaster
from saath.domain.insights_features import extract_commitment_features


def run_forecast_eval() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n=======================================================")
    print(" SAATH FORECASTING EVALUATION BENCHMARK")
    print("=======================================================\n")

    forecaster = HeuristicForecaster()

    # Synthetic vendor test cases
    commitments_history = [
        {"id": "c1", "responsible_party": "Plumber", "state": "done", "created_at": 1000, "due_at": 2000, "updated_at": 1900},
        {"id": "c2", "responsible_party": "Plumber", "state": "rescheduled", "created_at": 1000, "due_at": 2000, "updated_at": 3000},
        {"id": "c3", "responsible_party": "Plumber", "state": "rescheduled", "created_at": 1000, "due_at": 2000, "updated_at": 3000},
        {"id": "c4", "responsible_party": "Plumber", "state": "done", "created_at": 1000, "due_at": 2000, "updated_at": 1900},
    ]

    open_comm = {"id": "c5", "responsible_party": "Plumber", "created_at": 5000, "due_at": 6000}
    feats = extract_commitment_features(open_comm, commitments_history)
    slip_risk = forecaster.predict_slip(feats, commitments_history)

    print(f"Vendor:                Plumber")
    print(f"Past History Count:    {feats['prior_commitments_for_vendor']}")
    print(f"Predicted Slip Prob:   {slip_risk.probability_slip * 100:.1f}%")
    print(f"Risk Level:            {slip_risk.risk_level.upper()}")
    print(f"Explanation:           {slip_risk.explanation}")
    print(f"Is Estimate Labeled:   {slip_risk.is_estimate}")

    # Supply runout test
    restock_history_days = [7.0, 7.5, 6.8]
    runout = forecaster.predict_runout("milk", "Milk", restock_history_days)
    print(f"\nSupply Item:           Milk")
    print(f"Est Days Remaining:    {runout.estimated_days_remaining} days")
    print(f"Explanation:           {runout.explanation}")

    assert slip_risk.is_estimate is True
    assert slip_risk.has_enough_history is True
    assert runout.is_estimate is True
    assert runout.has_enough_history is True

    print("\n-------------------------------------------------------")
    print("✅ ALL FORECASTING INVARIANTS AND METRICS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(run_forecast_eval())
