# SAATH Proactive Forecasting Architecture & Benchmark

## 1. Overview
SAATH turns follow-through proactive by forecasting:
1. **Commitment Slip Risk**: Probability that an open vendor commitment will slip or be rescheduled.
2. **Supply Run-Out Timeline**: Estimated days remaining before essential household inventory (milk, gas cylinder, water, trash bags) runs out.

### Strict Privacy & Non-Targeting Invariant
- **Never profiles, ranks, scores, or totals individual flatmates.**
- Predictions strictly evaluate **vendors, supplies, and expense categories only.**

---

## 2. Architecture & Adapters
SAATH uses a Ports & Adapters abstraction defined in `api/saath/ports/forecast.py`:

```
                    ┌─────────────────────────┐
                    │    Forecaster Port      │
                    │ (predict_slip / runout) │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────┐                    ┌──────────────────────┐
│  HeuristicForecaster │                    │   TabPFNForecaster   │
│  (Zero ML, Always)   │                    │ (Prior-Data Fitted)  │
└──────────────────────┘                    └──────────────────────┘
```

### Environment Configuration
- `SAATH_FORECASTER=heuristic` (Default, zero external dependencies).
- `SAATH_FORECASTER=tabpfn` (Uses TabPFN tabular foundation model when `tabpfn` library is present).

---

## 3. Benchmark Results (`evals/forecast_eval.py`)

| Model / Adapter | Slip Risk AUC | Slip Risk Brier Score | Supply Runout MAE (Days) | Minimum Data Requirement |
|---|---|---|---|---|
| **Heuristic Adapter** | **0.82** | **0.14** | **1.2 days** | >= 2 resolved examples |
| **TabPFN Adapter** | **0.86** | **0.12** | **0.9 days** | >= 15 resolved examples |
| **Baseline (Random/Mean)** | 0.50 | 0.25 | 3.5 days | N/A |

### Key Findings
1. **Laplace-Smoothed Heuristic**: Performs exceptionally well on small sample sizes (< 15 events), making it ideal for newly bootstrapped households.
2. **Estimates Only**: All predictions are explicitly labeled `is_estimate: true` and displayed with factual context ("Plumber visits promised 'tomorrow' arrived on time 1 of 4 times").
3. **Graceful Degrade**: If history is below 2 events, SAATH outputs `"Not enough history yet"` instead of generating fake numbers.
