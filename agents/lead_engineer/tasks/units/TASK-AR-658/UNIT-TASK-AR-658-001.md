---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-658-001
work_uid: a3c404f7-ba45-431c-8062-50b5c3ece6c4
kind: unit
parent_id: TASK-AR-658
unit_id: UNIT-TASK-AR-658-001
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
summary: Guard every worker mutation and remove broad staging
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-656-002
  - UNIT-TASK-AR-657-002
  - UNIT-TASK-AR-659-001
escalation_triggers:
context: agent_loop checkpoint uses git add -A, and current claim metadata cannot prove that a commit or push belongs to one session.
inputs:
  - new:scripts/runtime_state_store.py
  - scripts/agent_loop.py
  - scripts/claim_guard.py
  - scripts/safe_ref_op.py
  - .codex/hooks.json
target_files:
  - new:scripts/session_scm_guard.py
  - scripts/agent_loop.py
  - scripts/claim_guard.py
  - scripts/safe_ref_op.py
  - .codex/hooks.json
  - new:tests/test_session_scm_guard.py
  - new:tests/test_agent_loop.py
  - tests/test_claim_guard.py
  - tests/test_safe_ref_op.py
  - src/agent_runtime/templates/project/scripts/agent_loop.py
scope: Validate cwd, real worktree, exact branch, lease token, staged paths, commit trailers, and push ref before every worker mutation. Do not implement merge-queue integration in this unit.
acceptance:
  - No broad staging command remains in worker recovery paths.
  - A worker cannot mutate a sibling or protected branch.
  - Stale lease generation fails at every mutation boundary.
  - A valid owned commit and push still work.
verification:
  - python -m pytest -q tests/test_session_scm_guard.py tests/test_agent_loop.py tests/test_claim_guard.py tests/test_safe_ref_op.py
handoff: Provide the allowed/blocked Git command matrix and exact-path checkpoint evidence.
stop_condition: Stop before granting worker access to merge or integrate sibling commits.
---

# UNIT-TASK-AR-658-001 - Guard every worker mutation and remove broad staging

## Context

agent_loop checkpoint uses git add -A, and current claim metadata cannot prove that a commit or push belongs to one session.

## Inputs

- new:scripts/runtime_state_store.py
- scripts/agent_loop.py
- scripts/claim_guard.py
- scripts/safe_ref_op.py
- .codex/hooks.json

## Target Files

- new:scripts/session_scm_guard.py
- scripts/agent_loop.py
- scripts/claim_guard.py
- scripts/safe_ref_op.py
- .codex/hooks.json
- new:tests/test_session_scm_guard.py
- new:tests/test_agent_loop.py
- tests/test_claim_guard.py
- tests/test_safe_ref_op.py
- src/agent_runtime/templates/project/scripts/agent_loop.py

## Scope

Validate cwd, real worktree, exact branch, lease token, staged paths, commit trailers, and push ref before every worker mutation. Do not implement merge-queue integration in this unit.

## Steps

1. Create negative fixtures for git add -A, commit -a, pull, merge, rebase, cherry-pick, and foreign ref push.
2. Replace checkpoint broad staging with the session-owned actual delta.
3. Require session, run, claim, and unit provenance trailers.
4. Allow only HEAD to the exact claimed remote branch with expected-old-SHA protection.
5. Revalidate the fencing token in hooks, pre-commit, and pre-push.

## Acceptance Criteria

- No broad staging command remains in worker recovery paths.
- A worker cannot mutate a sibling or protected branch.
- Stale lease generation fails at every mutation boundary.
- A valid owned commit and push still work.

## Verification

- `python -m pytest -q tests/test_session_scm_guard.py tests/test_agent_loop.py tests/test_claim_guard.py tests/test_safe_ref_op.py`

## Handoff

Provide the allowed/blocked Git command matrix and exact-path checkpoint evidence.

## Stop Boundary

Stop before granting worker access to merge or integrate sibling commits.
