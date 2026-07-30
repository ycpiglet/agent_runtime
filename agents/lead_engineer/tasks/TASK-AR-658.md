---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-658
display_id: TASK-AR-658
task_uid: 366ff497-78fc-4032-9de9-9b035eddda07
work_id: TASK-AR-658
work_uid: 366ff497-78fc-4032-9de9-9b035eddda07
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Enforce session-owned SCM and quarantine foreign state
status: planned
priority: P0
difficulty: XL
est_hours: 24
est_tokens: 50000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-658/UNIT-TASK-AR-658-001.md
reservation_id: RES-20260730-112517-91ed5cf4-04
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Prevent a writer from staging, committing, pulling, merging, pushing, reverting, or closing over work owned by another session.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - One mutating session owns exactly one worktree and branch.
  - Worker Git operations are restricted to owned paths, commits, and the claimed remote ref.
  - Broad staging and worker pull/merge/rebase/cherry-pick are blocked.
  - Sibling worktree or branch progress is classified as foreign observation and does not block closeout.
  - Unexpected changes inside the owned worktree fail with attributable ownership evidence.
verification:
  - python -m pytest -q tests/test_session_scm_guard.py tests/test_agent_loop.py tests/test_stop_hook_session_scope.py tests/test_session_baseline.py tests/test_dirty_intake.py tests/test_closure_gate.py
---

# TASK-AR-658 - Enforce session-owned SCM and quarantine foreign state

## Goal

- Prevent a writer from staging, committing, pulling, merging, pushing, reverting, or closing over work owned by another session.

## Scope

- Add a session SCM guard, exact-path staging, commit provenance, branch/ref ownership, foreign-state classification, and session-local dirty/closure behavior. Integration authority remains a separate role.

## Acceptance Criteria

- One mutating session owns exactly one worktree and branch.
- Worker Git operations are restricted to owned paths, commits, and the claimed remote ref.
- Broad staging and worker pull/merge/rebase/cherry-pick are blocked.
- Sibling worktree or branch progress is classified as foreign observation and does not block closeout.
- Unexpected changes inside the owned worktree fail with attributable ownership evidence.

## Verification

- `python -m pytest -q tests/test_session_scm_guard.py tests/test_agent_loop.py tests/test_stop_hook_session_scope.py tests/test_session_baseline.py tests/test_dirty_intake.py tests/test_closure_gate.py`
