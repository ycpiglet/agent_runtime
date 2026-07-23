---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-621-001
work_uid: 74ac5494-c588-43f1-8ae7-47d7ec88d509
kind: unit
parent_id: TASK-AR-621
unit_id: UNIT-TASK-AR-621-001
task_id: TASK-AR-621
task_set_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
initiative_id: INIT-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead-engineer
created_at: 2026-07-23T14:08:00+09:00
updated_at: 2026-07-23T15:51:06+09:00
origin_type: runtime_bug
origin_ref: reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md
created_by: codex-root-planner
summary: Define and test cross-platform verification execution
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - cross_platform
  - data_integrity
  - runtime
context: TASK-AR-602 demonstrated that subprocess.run with shell=True lets cmd.exe consume the caret in an annotated-tag peel expression even though the command is correct in the work record.
inputs:
  - reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md
  - reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202.json
  - scripts/work.py
  - tests/test_work_verify.py
target_files:
  - scripts/work.py
  - tests/test_work_verify.py
  - reviews/
scope: Define the intended command execution contract, add a Windows-relevant regression, and make the smallest runner change that preserves command arguments without weakening evidence capture or timeout behavior.
acceptance:
  - The regression fails against the current Windows runner and passes after the fix.
  - Success, nonzero exit, and timeout results retain their current evidence schema.
  - No historical verification record is rewritten or removed.
verification:
  - python -m pytest tests/test_work_verify.py -q
  - python scripts/owner_governance_gate.py
handoff: Report the reproduced command mutation, chosen execution contract, focused test results, governance result, and any compatibility limitation.
stop_condition: Stop before changing the verification evidence schema, accepting arbitrary untrusted commands from a new source, or rewriting historical evidence.
verified_at: 2026-07-23T15:51:06+09:00
verified_by: /root/task-ar-621
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106.json
---

# UNIT-TASK-AR-621-001 - Define and test cross-platform verification execution

## Context

TASK-AR-602 demonstrated that subprocess.run with shell=True lets cmd.exe consume the caret in an annotated-tag peel expression even though the command is correct in the work record.

## Inputs

- reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md
- reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202.json
- scripts/work.py
- tests/test_work_verify.py

## Target Files

- scripts/work.py
- tests/test_work_verify.py
- reviews/

## Scope

Define the intended command execution contract, add a Windows-relevant regression, and make the smallest runner change that preserves command arguments without weakening evidence capture or timeout behavior.

## Steps

1. Reproduce the caret mutation through the current verification runner.
2. Add regression coverage for metacharacter preservation and existing result capture.
3. Implement the cross-platform execution contract and run focused plus governance verification.

## Acceptance Criteria

- The regression fails against the current Windows runner and passes after the fix.
- Success, nonzero exit, and timeout results retain their current evidence schema.
- No historical verification record is rewritten or removed.

## Verification

- `python -m pytest tests/test_work_verify.py -q`
- `python scripts/owner_governance_gate.py`

## Handoff

Report the reproduced command mutation, chosen execution contract, focused test results, governance result, and any compatibility limitation.

## Stop Boundary

Stop before changing the verification evidence schema, accepting arbitrary untrusted commands from a new source, or rewriting historical evidence.
