---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-601-001
work_uid: 12fcc40e-3ccd-4182-ba04-839127cd68e6
kind: unit
parent_id: TASK-AR-601
unit_id: UNIT-TASK-AR-601-001
task_id: TASK-AR-601
task_set_id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
initiative_id: INIT-AR-HOOK-PORTABILITY-CLEANUP
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-20T12:56:05+09:00
updated_at: 2026-07-20T13:09:38+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md
created_by: codex-root
summary: Make hook execution portable and close the worktree lifecycle
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Linux checkout uses a tracked .codex/hooks.json with Windows absolute Python paths and .cmd commands, while root .githooks are tracked as non-executable and core.hooksPath is unset.
inputs:
  - .codex/hooks.json
  - src/agent_runtime/templates/project/.codex/hooks.json
  - .githooks/pre-commit
  - .githooks/post-merge
  - scripts/bootstrap_dev_env.py
  - docs/DEV-ENVIRONMENT.md
target_files:
  - .codex/hooks.json
  - src/agent_runtime/templates/project/.codex/hooks.json
  - .githooks/pre-commit
  - .githooks/post-merge
  - tests/test_stop_hook_owner_governance.py
  - tests/test_session_dashboard.py
  - tests/test_update_notify.py
  - tests/test_lock_merge_driver.py
  - tests/fixtures/host/agent_runtime.lock.json
  - src/agent_runtime/templates/project/CLAUDE.md
  - src/agent_runtime/templates/project/AGENTS.md
  - reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md
scope: Use portable Python hook commands, preserve existing hook semantics/timeouts, record executable Git hook modes, install the documented local configuration, and remove only lifecycle artifacts created by this task.
acceptance:
  - Hook manifests execute through portable Python commands on the current Linux host.
  - Root and template Git hook files are executable in Git metadata.
  - Bootstrap reports hooksPath and editable install as healthy.
  - No unrelated open issue or TASK-AR-600 implementation is changed.
verification:
  - python -m pytest tests/test_stop_hook_owner_governance.py tests/test_session_dashboard.py tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
  - python scripts/lock_merge_driver.py pre-commit
  - python scripts/bootstrap_dev_env.py
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
handoff: Report the task and unit IDs, exact hook root cause, changed manifests/modes, test results, independent verifier evidence, final branch status, and any unrelated deferred findings.
stop_condition: Stop on destructive reset, force-push, unrelated GitHub issue remediation, workflow/secret changes, or any conflict with user-authored uncommitted content.
verified_at: 2026-07-20T13:09:38+09:00
verified_by: le-20260720-125746-kst-hookfix
evidence_refs:
  - reviews/VERIFY-2026-07-20-unit-task-ar-601-001-20260720130938.json
---

# UNIT-TASK-AR-601-001 - Make hook execution portable and close the worktree lifecycle

## Context

The Linux checkout uses a tracked .codex/hooks.json with Windows absolute Python paths and .cmd commands, while root .githooks are tracked as non-executable and core.hooksPath is unset.

## Inputs

- .codex/hooks.json
- src/agent_runtime/templates/project/.codex/hooks.json
- .githooks/pre-commit
- .githooks/post-merge
- scripts/bootstrap_dev_env.py
- docs/DEV-ENVIRONMENT.md

## Target Files

- .codex/hooks.json
- src/agent_runtime/templates/project/.codex/hooks.json
- .githooks/pre-commit
- .githooks/post-merge
- tests/test_stop_hook_owner_governance.py
- tests/test_session_dashboard.py
- tests/test_update_notify.py
- tests/test_lock_merge_driver.py
- tests/fixtures/host/agent_runtime.lock.json
- src/agent_runtime/templates/project/CLAUDE.md
- src/agent_runtime/templates/project/AGENTS.md
- reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md

## Scope

Use portable Python hook commands, preserve existing hook semantics/timeouts, record executable Git hook modes, install the documented local configuration, and remove only lifecycle artifacts created by this task.

## Steps

1. Add regression tests that reject absolute Windows paths and .cmd dependencies in Codex hook manifests and require executable Git hooks.
2. Update live and host-template hook manifests and Git hook modes.
3. Apply bootstrap configuration and run focused verification.
4. Write self-verification and obtain independent W4b verification before merge and cleanup.
5. Reconcile the dedicated update-notify contract and template documentation if independent verification finds stale Windows-only expectations.

## Acceptance Criteria

- Hook manifests execute through portable Python commands on the current Linux host.
- Root and template Git hook files are executable in Git metadata.
- Bootstrap reports hooksPath and editable install as healthy.
- No unrelated open issue or TASK-AR-600 implementation is changed.

## Verification

- `python -m pytest tests/test_stop_hook_owner_governance.py tests/test_session_dashboard.py tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`
- `python scripts/lock_merge_driver.py pre-commit`
- `python scripts/bootstrap_dev_env.py`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

## Handoff

Report the task and unit IDs, exact hook root cause, changed manifests/modes, test results, independent verifier evidence, final branch status, and any unrelated deferred findings.

## Stop Boundary

Stop on destructive reset, force-push, unrelated GitHub issue remediation, workflow/secret changes, or any conflict with user-authored uncommitted content.
