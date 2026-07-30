---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-657-001
work_uid: 01b1d6af-a002-4240-96bb-e94d25731e0f
kind: unit
parent_id: TASK-AR-657
unit_id: UNIT-TASK-AR-657-001
task_id: TASK-AR-657
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Build the canonical control-plane store and fenced lease primitive
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: Claim conflict checks and persistence are separate operations, and tracked worktrees hold divergent snapshots of active claims. A local canonical store must serialize acquisition across linked worktrees.
inputs:
  - new:scripts/runtime_state_store.py
  - scripts/claim_lease.py
  - scripts/parallel_worktree_gate.py
  - scripts/multi_host_claim_gate.py
target_files:
  - new:scripts/runtime_state_store.py
  - scripts/claim_lease.py
  - scripts/multi_host_claim_gate.py
  - new:tests/test_runtime_state_store.py
  - tests/test_claim_lease.py
  - tests/test_multi_host_claim_gate.py
  - new:docs/runtime-control-plane.md
scope: Implement a Git-common-dir SQLite WAL or equivalently locked transactional adapter with unique live-owner constraints and fencing generation. Define an adapter contract for a future multi-host CAS backend.
acceptance:
  - Concurrent acquisition has one committed winner.
  - Expired ownership can be recovered only with a higher fencing token.
  - Partial writes and process death preserve a consistent store.
  - The store is shared by linked worktrees but absent from product Git history.
verification:
  - python -m pytest -q tests/test_runtime_state_store.py tests/test_claim_lease.py tests/test_multi_host_claim_gate.py
handoff: Provide transaction traces for simultaneous acquisition, stale-token rejection, and crash recovery.
stop_condition: Stop before changing worker Git command authorization.
---

# UNIT-TASK-AR-657-001 - Build the canonical control-plane store and fenced lease primitive

## Context

Claim conflict checks and persistence are separate operations, and tracked worktrees hold divergent snapshots of active claims. A local canonical store must serialize acquisition across linked worktrees.

## Inputs

- new:scripts/runtime_state_store.py
- scripts/claim_lease.py
- scripts/parallel_worktree_gate.py
- scripts/multi_host_claim_gate.py

## Target Files

- new:scripts/runtime_state_store.py
- scripts/claim_lease.py
- scripts/multi_host_claim_gate.py
- new:tests/test_runtime_state_store.py
- tests/test_claim_lease.py
- tests/test_multi_host_claim_gate.py
- new:docs/runtime-control-plane.md

## Scope

Implement a Git-common-dir SQLite WAL or equivalently locked transactional adapter with unique live-owner constraints and fencing generation. Define an adapter contract for a future multi-host CAS backend.

## Steps

1. Write concurrent-process acquisition and crash fixtures.
2. Define versioned session, goal, claim, heartbeat, and projection tables.
3. Enforce unique active ownership for task, worktree realpath, branch, and declared semantic domain.
4. Increment fencing generation on every reacquisition.
5. Expose read-only status and recovery diagnostics.

## Acceptance Criteria

- Concurrent acquisition has one committed winner.
- Expired ownership can be recovered only with a higher fencing token.
- Partial writes and process death preserve a consistent store.
- The store is shared by linked worktrees but absent from product Git history.

## Verification

- `python -m pytest -q tests/test_runtime_state_store.py tests/test_claim_lease.py tests/test_multi_host_claim_gate.py`

## Handoff

Provide transaction traces for simultaneous acquisition, stale-token rejection, and crash recovery.

## Stop Boundary

Stop before changing worker Git command authorization.
