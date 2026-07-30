---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-657
display_id: TASK-AR-657
task_uid: dbd03c85-27cf-4482-a15c-40ccc497adbd
work_id: TASK-AR-657
work_uid: dbd03c85-27cf-4482-a15c-40ccc497adbd
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Make session and claim ownership atomic and durable
status: planned
priority: P0
difficulty: XL
est_hours: 22
est_tokens: 46000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-657/UNIT-TASK-AR-657-001.md
reservation_id: RES-20260730-112517-91ed5cf4-03
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Give each writer one exclusive session, worktree, branch, and fenced claim lease without advancing a source branch.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Two simultaneous acquisitions for one task, worktree, branch, or semantic domain produce exactly one winner.
  - Every writer lease includes session, run, worktree realpath, branch, base SHA, generation, fencing token, and expiry.
  - Claim creation and heartbeats do not change Git HEAD or status.
  - A stale token cannot mutate or release a newer lease.
  - Existing tracked claim history can be read and migrated without fabricating ownership.
verification:
  - python -m pytest -q tests/test_runtime_state_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py tests/test_parallel_worktree_gate.py tests/test_multi_host_claim_gate.py
---

# TASK-AR-657 - Make session and claim ownership atomic and durable

## Goal

- Give each writer one exclusive session, worktree, branch, and fenced claim lease without advancing a source branch.

## Scope

- Build a canonical local control-plane store under the Git common directory, issue monotonic fencing tokens, make claim acquisition transactional, remove live-state autocommit, and preserve read-only projections for operators.

## Acceptance Criteria

- Two simultaneous acquisitions for one task, worktree, branch, or semantic domain produce exactly one winner.
- Every writer lease includes session, run, worktree realpath, branch, base SHA, generation, fencing token, and expiry.
- Claim creation and heartbeats do not change Git HEAD or status.
- A stale token cannot mutate or release a newer lease.
- Existing tracked claim history can be read and migrated without fabricating ownership.

## Verification

- `python -m pytest -q tests/test_runtime_state_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py tests/test_parallel_worktree_gate.py tests/test_multi_host_claim_gate.py`
