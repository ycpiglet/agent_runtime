---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-598-001
work_uid: e9ba5313-09c9-4576-a41b-df5ca6bf7fd3
kind: unit
parent_id: TASK-AR-598
unit_id: UNIT-TASK-AR-598-001
task_id: TASK-AR-598
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T12:28:43+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Rebase and verify session resume recovery
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - cross_cutting
  - data_integrity
context: PR
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/274
  - https://github.com/ycpiglet/agent_runtime/pull/277
  - src/agent_runtime/templates/project/.codex/hooks.json
target_files:
  - src/agent_runtime/templates/project/.codex/hooks.json
  - new:src/agent_runtime/templates/project/scripts/session_resume_check.py
  - new:tests/test_session_resume_check.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Integrate the PR implementation on current main, resolve only relevant conflicts, keep report-only defaults, and prove hook order and malformed-state safety.
acceptance:
  - SessionStart prints resumable state when present and never fails startup by default.
  - Hook ordering is update notify -> dashboard -> reaper -> interrupted detector -> resume check.
  - Focused crash recovery tests pass.
verification:
  - python -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report PR conflict resolution, hook order, malformed-state tests, and the remote issue/PR outcome.
stop_condition: Stop if the PR contains host-specific behavior or destructive recovery; retain report-only behavior and document the incompatible portion.
verified_at: 2026-07-19T12:28:43+09:00
verified_by: codex-root-task-ar-598
evidence_refs:
  - reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719122843.json
---

# UNIT-TASK-AR-598-001 - Rebase and verify session resume recovery

## Context

PR #277 contains a host-proven 673-line session resume auditor but is DIRTY against current main; issue #274 part 1 atomic writes already landed via PR #276.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/274
- https://github.com/ycpiglet/agent_runtime/pull/277
- src/agent_runtime/templates/project/.codex/hooks.json

## Target Files

- src/agent_runtime/templates/project/.codex/hooks.json
- new:src/agent_runtime/templates/project/scripts/session_resume_check.py
- new:tests/test_session_resume_check.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Integrate the PR implementation on current main, resolve only relevant conflicts, keep report-only defaults, and prove hook order and malformed-state safety.

## Steps

1. Fetch PR #277 and compare its files with current main.
2. Apply the session auditor and hook wiring while preserving newer hook changes.
3. Run focused tests and host fixture lock validation, then reconcile the remote PR/issue.

## Acceptance Criteria

- SessionStart prints resumable state when present and never fails startup by default.
- Hook ordering is update notify -> dashboard -> reaper -> interrupted detector -> resume check.
- Focused crash recovery tests pass.

## Verification

- `python -m pytest tests/test_session_resume_check.py tests/test_orchestrator_atomic_writes.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report PR conflict resolution, hook order, malformed-state tests, and the remote issue/PR outcome.

## Stop Boundary

Stop if the PR contains host-specific behavior or destructive recovery; retain report-only behavior and document the incompatible portion.