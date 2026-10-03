# SAATH Evaluation & Benchmark Results

- **Date**: 2026-10-04 00:30:13
- **Model**: `gemma2:2b`
- **Hardware**: Windows 11 (AMD64)

### Comparative Performance Table

| Dataset | Parser Mode | Type Accuracy | Money Exactness | Injection Block Rate | Latency P50 (ms) | Fallback Rate |
|---|---|---|---|---|---|---|
| Golden (Regression) | Rules Only | 100.0% | 100.0% | 100.0% | 0.01 | 0.0% |
| Golden (Regression) | Production (gemma2:2b) | 26.7% | 66.7% | 100.0% | 2534.99 | 100.0% |
| Held-Out v1 | Rules Only | 56.0% | 87.5% | 100.0% | 0.01 | 0.0% |
| Held-Out v1 | Production (gemma2:2b) | 31.0% | 45.8% | 100.0% | 2837.97 | 100.0% |


### Security & Safety Invariants Verified
1. **False Financial Auto-Apply Rate**: Exactly **0.0%** across all sets (money requires human confirmation).
2. **Prompt Injection Bypasses**: Exactly **0.0%** across all sets.
3. **Graceful Fallback**: Unreachable local LLM degrades safely to rule engine without throwing 500 errors.
