# ADR 0003: Paise Money Representation and Largest-Remainder Split

## Status
Accepted

## Context
Floating point calculations introduce rounding drift, precision loss, and non-deterministic split sum errors (e.g. ₹100 split 3 ways becoming 33.33 + 33.33 + 33.33 = 99.99). In a flat, a missing rupee or penny causes annoyance and mistrust.

## Decision
1. All monetary values are represented strictly as 64-bit signed integers denoting **paise** (1 INR = 100 paise). Floating point types are prohibited in domain schemas, database tables, and API contracts.
2. Group splits apply the deterministic **Largest-Remainder Method (Hare-Niemeyer)**:
   - Base share = `floor(total_paise / n)`
   - Remainder = `total_paise % n`
   - Remainder paise are distributed +1 to participants sorted by member ID (or stable order) until exhausted.
3. Every split guarantees the invariant: `sum(shares) == total_paise` exactly.
4. Validation bounds: single expense amounts must lie within `[1, 10,000,000]` paise (₹0.01 to ₹100,000.00).

## Consequences
- Property tests with Hypothesis can mathematically prove sum conservation across any participant count and amount.
- Zero floating-point rounding errors.
