---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-606-001
work_uid: 784b1296-c547-4d2d-8d2a-4bc6156186db
kind: unit
parent_id: TASK-AR-606
unit_id: UNIT-TASK-AR-606-001
task_id: TASK-AR-606
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T17:45:00+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Make hook activation executable and idempotent
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - security
  - cross_platform
  - external_effect
context: GitHub issue 295 shows core.hooksPath alone is insufficient on POSIX because both tracked hooks have mode 100644. Archive/install paths may also lose executable metadata, so installation must repair it safely.
inputs:
  - reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
  - .githooks/pre-commit
  - scripts/lock_merge_driver.py
  - scripts/bootstrap_dev_env.py
target_files:
  - .githooks/pre-commit
  - src/agent_runtime/templates/project/.githooks/pre-commit
  - scripts/lock_merge_driver.py
  - src/agent_runtime/templates/project/scripts/lock_merge_driver.py
  - scripts/bootstrap_dev_env.py
  - tests/test_lock_merge_driver.py
  - tests/test_bootstrap_dev_env.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Set and verify executable activation for the configured pre-commit hook and make installers repair it on POSIX. Do not add new hook policy or change gate semantics.
acceptance:
  - POSIX Git executes the configured hook after installation.
  - Repeated installation is safe and Windows does not fail on chmod handling.
verification:
  - python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit
handoff: Report Git modes, installer behavior on POSIX/Windows, tests, and GitHub issue 295 evidence.
stop_condition: Stop before changing hook contents or enabling any additional hook.
---

# UNIT-TASK-AR-606-001 - Make hook activation executable and idempotent

## Context

GitHub #295 shows core.hooksPath alone is insufficient on POSIX because both tracked hooks have mode 100644. Archive/install paths may also lose executable metadata, so installation must repair it safely.

## Inputs

- reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
- .githooks/pre-commit
- scripts/lock_merge_driver.py
- scripts/bootstrap_dev_env.py

## Target Files

- .githooks/pre-commit
- src/agent_runtime/templates/project/.githooks/pre-commit
- scripts/lock_merge_driver.py
- src/agent_runtime/templates/project/scripts/lock_merge_driver.py
- scripts/bootstrap_dev_env.py
- tests/test_lock_merge_driver.py
- tests/test_bootstrap_dev_env.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Set and verify executable activation for the configured pre-commit hook and make installers repair it on POSIX. Do not add new hook policy or change gate semantics.

## Steps

1. Add mode/installer failure-first tests.
2. Set tracked executable modes and add idempotent POSIX repair.
3. Verify Windows-safe behavior and regenerate the host lock.

## Acceptance Criteria

- POSIX Git executes the configured hook after installation.
- Repeated installation is safe and Windows does not fail on chmod handling.

## Verification

- `python -m pytest tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `git ls-files -s .githooks/pre-commit src/agent_runtime/templates/project/.githooks/pre-commit`

## Handoff

Report Git modes, installer behavior on POSIX/Windows, tests, and issue #295 evidence.

## Stop Boundary

Stop before changing hook contents or enabling any additional hook.
