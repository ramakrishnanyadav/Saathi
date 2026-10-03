# ADR 0002: Derived Overdue State and Time Independence

## Status
Accepted

## Context
Commitments in household systems often slip. Storing an `is_overdue` boolean flag in the database requires background cron jobs or daemon polls to constantly sweep and mutate rows as time advances. If the server is offline or restarts, flags become stale. Furthermore, testing and interactive time simulation (e.g., Demo time scrubber) become complex and error-prone if time jumps require modifying database records.

## Decision
Overdue is strictly a derived property, computed at query time:
`is_overdue := (state == 'waiting' AND due_at < now)`

The database schema stores only `state` (`waiting`, `done`, `rescheduled`, `cancelled`) and `due_at` (epoch ms). There is NO stored overdue flag.
An index on `(house_id, state, due_at)` allows instant index scans for attention queries:
`WHERE house_id = :h AND state = 'waiting' AND due_at < :now ORDER BY due_at ASC`

All internal services accept an injected `Clock` protocol. Advancing time in tests or the demo scrubber (`SimClock.advance(delta)`) immediately reflects overdue status without modifying a single row.

## Consequences
- Zero stale overdue flags across restarts or offline periods.
- O(log n + k) query efficiency via partial B-tree index.
- Clean time-travel simulation in 90-second demo and property tests.
