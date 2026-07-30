---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-658-002
work_uid: 5d453e6d-6c03-4b3f-ab81-2bb416cadba2
kind: unit
parent_id: TASK-AR-658
unit_id: UNIT-TASK-AR-658-002
task_id: TASK-AR-658
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
summary: Make dirty, stop, and closeout decisions session-local
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-658-001
escalation_triggers:
context: The current Stop helper infers touched paths from transcripts and repo-wide gates see every claim, branch, and worktree. This turns valid sibling work into a recurring unknown-change bottleneck.
inputs:
  - new:scripts/session_scm_guard.py
  - scripts/session_baseline.py
  - scripts/stop_hook_session_scope.py
  - scripts/dirty_intake.py
  - scripts/closure_gate.py
  - scripts/parallel_worktree_gate.py
target_files:
  - scripts/session_baseline.py
  - scripts/stop_hook_session_scope.py
  - scripts/dirty_intake.py
  - scripts/closure_gate.py
  - scripts/parallel_worktree_gate.py
  - tests/test_session_baseline.py
  - tests/test_stop_hook_session_scope.py
  - tests/test_dirty_intake.py
  - tests/test_closure_gate.py
  - tests/test_parallel_worktree_gate.py
scope: Compute owned change from manifest plus base-to-HEAD and worktree delta, classify foreign state, and restrict closeout obligations to the current session. Do not hide unattributed edits in the owned worktree.
acceptance:
  - Two dirty sibling worktrees can close independently.
  - origin/main advancement is external base progress, not an unknown local edit.
  - A sibling-only commit never enters this session's closeout set.
  - A true same-worktree intrusion still blocks with owner/claim detail.
verification:
  - python -m pytest -q tests/test_session_baseline.py tests/test_stop_hook_session_scope.py tests/test_dirty_intake.py tests/test_closure_gate.py tests/test_parallel_worktree_gate.py
handoff: Show the classification matrix and a two-session closeout regression with no reciprocal blocking.
stop_condition: Stop if the implementation would downgrade unattributed edits in the current owned worktree.
---

# UNIT-TASK-AR-658-002 - Make dirty, stop, and closeout decisions session-local

## Context

The current Stop helper infers touched paths from transcripts and repo-wide gates see every claim, branch, and worktree. This turns valid sibling work into a recurring unknown-change bottleneck.

## Inputs

- new:scripts/session_scm_guard.py
- scripts/session_baseline.py
- scripts/stop_hook_session_scope.py
- scripts/dirty_intake.py
- scripts/closure_gate.py
- scripts/parallel_worktree_gate.py

## Target Files

- scripts/session_baseline.py
- scripts/stop_hook_session_scope.py
- scripts/dirty_intake.py
- scripts/closure_gate.py
- scripts/parallel_worktree_gate.py
- tests/test_session_baseline.py
- tests/test_stop_hook_session_scope.py
- tests/test_dirty_intake.py
- tests/test_closure_gate.py
- tests/test_parallel_worktree_gate.py

## Scope

Compute owned change from manifest plus base-to-HEAD and worktree delta, classify foreign state, and restrict closeout obligations to the current session. Do not hide unattributed edits in the owned worktree.

## Steps

1. Record session, run, claim, worktree, branch, base, and initial HEAD in the baseline.
2. Classify owned, expected-generated, foreign-observed, overlap, external-base-progress, and unattributed changes.
3. Make sibling state informational unless it overlaps an owned path or semantic domain.
4. Route attributable foreign findings to the owner session instead of halting the observer.
5. Keep unattributed owned-worktree edits blocking.

## Acceptance Criteria

- Two dirty sibling worktrees can close independently.
- origin/main advancement is external base progress, not an unknown local edit.
- A sibling-only commit never enters this session's closeout set.
- A true same-worktree intrusion still blocks with owner/claim detail.

## Verification

- `python -m pytest -q tests/test_session_baseline.py tests/test_stop_hook_session_scope.py tests/test_dirty_intake.py tests/test_closure_gate.py tests/test_parallel_worktree_gate.py`

## Handoff

Show the classification matrix and a two-session closeout regression with no reciprocal blocking.

## Stop Boundary

Stop if the implementation would downgrade unattributed edits in the current owned worktree.
