# MEETING (2026-06-09) - TASK-AR-225 source publication hygiene

## Attendees

- lead-engineer
- qa
- doc-steward
- independent-auditor

## Context

- `TASK-AR-224` produced executable proof:
  - context packet generation succeeded
  - fixture release-preflight executed
  - release-preflight returned `findings=358`
- The result proves the gate works, but it blocks `v0.1.8` readiness.

## Decision

1. Create `TASK-AR-225` as a P0 follow-up.
2. Treat host-only governance records as package publication blockers unless explicitly moved behind a host-only boundary.
3. Treat absolute local paths as publish blockers in any publishable artifact.
4. Keep `TASK-AR-223` in progress until `TASK-AR-225` either resolves or formally routes blockers to `hold_for_data`.

## Next Action

- Start with the smallest source publication fix: determine whether root-level `agents/lead_engineer/tasks` and `reviews` should be excluded from clean source or converted into package docs.
