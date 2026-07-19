---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-597-001
work_uid: 102e3195-e02b-4362-93c5-f26f5d5b0948
kind: unit
parent_id: TASK-AR-597
unit_id: UNIT-TASK-AR-597-001
task_id: TASK-AR-597
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T12:12:42+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Add diagnostic Git helper failures
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: GitHub
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/285
  - tests/test_release_auto_noncritical.py
target_files:
  - tests/test_release_auto_noncritical.py
scope: Refactor the local _git test helper to retain diagnostics and add a direct failure-message test.
acceptance:
  - The reproduced failing command emits its stderr in the assertion text.
  - The complete release-auto test module passes.
verification:
  - python -m pytest tests/test_release_auto_noncritical.py -q
handoff: Report a sample sanitized failure message and test output.
stop_condition: Stop if exposing stderr could leak credentials; sanitize sensitive command arguments before including them.
verified_at: 2026-07-19T12:12:42+09:00
verified_by: codex-root-task-ar-597
evidence_refs:
  - reviews/VERIFY-2026-07-19-unit-task-ar-597-001-20260719121242.json
---

# UNIT-TASK-AR-597-001 - Add diagnostic Git helper failures

## Context

GitHub #285 records an exit-128 git commit failure whose stderr was captured but omitted from pytest's CalledProcessError display.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/285
- tests/test_release_auto_noncritical.py

## Target Files

- tests/test_release_auto_noncritical.py

## Scope

Refactor the local _git test helper to retain diagnostics and add a direct failure-message test.

## Steps

1. Capture the completed process without immediately discarding output.
2. Raise a deterministic assertion containing command, code, stdout, and stderr on failure.
3. Add a unit test for the diagnostic contract and run the module.

## Acceptance Criteria

- The reproduced failing command emits its stderr in the assertion text.
- The complete release-auto test module passes.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py -q`

## Handoff

Report a sample sanitized failure message and test output.

## Stop Boundary

Stop if exposing stderr could leak credentials; sanitize sensitive command arguments before including them.