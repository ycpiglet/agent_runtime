---
id: TASK-AR-552
display_id: TASK-AR-552
task_uid: 7556ca8e-de5f-44fd-b9ed-42d80495c448
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - reliability
  - testing
  - deadlock
  - concurrency
---

# TASK-AR-552 - claim_reaper concurrency + heartbeat stress tests

## Goal

- The deadlock guardrails (claim_reaper/goal_supervisor) are unit-tested on the happy path, but live-worker failover under concurrency is under-tested. Add stress tests for heartbeat refresh, grace boundaries, and concurrent reaper races.

## Scope

### Input
- `scripts/claim_reaper.py`, `scripts/claim_lease.py`, `scripts/goal_supervisor.py`.
- Verification cases VC-REAP-3/4/13/19, VC-SUP-5/6.

### Process
- Simulate: a worker hanging but its lease still refreshing (must NOT reap); heartbeat delay spikes near the grace boundary; two reaper processes racing on one claim file (atomic write, no corruption).
- Add a latency policy on `tests/test_claim_reaper.py` similar to the message_queue policy.

### Output
- New concurrency/stress tests + optional latency gate.

## Acceptance Criteria

- A live-but-slow worker (lease refreshing) is never reaped across the stress window.
- Grace-boundary cases (`now == deadline+grace`) are deterministic.
- Concurrent reaping leaves valid JSON (no partial writes); idempotent.

## Evidence Targets

- New tests + CI run; mapping to VC-REAP/VC-SUP ids.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`; `docs/deadlock-guardrails.md`.
