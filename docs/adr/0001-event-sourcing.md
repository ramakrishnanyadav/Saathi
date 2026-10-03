# ADR 0001: Append-Only Event Sourcing for Household State

## Status
Accepted

## Context
In a shared household, the mental load is fraught with disagreement about what happened, who promised what, and when. An audit trail of immutable events ensures:
1. Complete transparency and dispute resolution.
2. Conflict-free offline merge from multiple devices over local LAN.
3. Safe "Undo" without destructive data loss (superseding events).
4. Replay equivalence: projections can be rebuilt deterministically from genesis.

## Decision
All household facts are stored in an append-only `event` table with SQLite `BEFORE UPDATE` and `BEFORE DELETE` triggers that execute `RAISE(ABORT, 'events are immutable')`.
Corrections and cancellations emit superseding events with `supersedes_id` referencing the target event.
Projections (`commitment`, `issue`, `expense`, `supply`, `action_log`) are materialized asynchronously or in the same transaction for read efficiency O(log n + k).

## Consequences
- High auditability and offline synchronization via monotonically ordered events (`occurred_at`, `id`).
- Projections are ephemeral caches; schema changes can be adopted by replaying history in streamed batches (O(E)).
- Storage overhead is minimal for household scales (thousands of events per year = a few megabytes).
