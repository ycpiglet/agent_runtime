---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-596-001
work_uid: f55f6202-8263-4b16-8a19-3394b80b3db8
kind: unit
parent_id: TASK-AR-596
unit_id: UNIT-TASK-AR-596-001
task_id: TASK-AR-596
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T10:28:06+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
created_by: codex-root-planner
summary: Implement task-ID-aware pointer resolution
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: GitHub #290 reports pointer-task-missing when active_task is TASK-231 and the canonical file is TASK-231-taskset-dispatcher-selection-order.md.
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/290
  - scripts/conversation_work_audit.py
  - tests/test_conversation_work_audit.py
target_files:
  - scripts/conversation_work_audit.py
  - src/agent_runtime/templates/project/scripts/conversation_work_audit.py
  - tests/test_conversation_work_audit.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Resolve exact and slugged task filenames by canonical frontmatter ID or boundary-safe filename prefix, mirror the implementation, and test false-positive boundaries.
acceptance:
  - Slugged canonical task files satisfy pointer audit.
  - Prefix collisions do not satisfy pointer audit.
  - Focused tests and the live audit pass.
verification:
  - python -m pytest tests/test_conversation_work_audit.py -q
  - python scripts/conversation_work_audit.py --check
handoff: Report resolver semantics, collision coverage, and audit output.
stop_condition: Stop if multiple canonical files claim the same task ID; surface the ambiguity rather than choosing one silently.
---

# UNIT-TASK-AR-596-001 - Implement task-ID-aware pointer resolution

## Context

GitHub #290 reports pointer-task-missing when active_task is TASK-231 and the canonical file is TASK-231-taskset-dispatcher-selection-order.md.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/290
- scripts/conversation_work_audit.py
- tests/test_conversation_work_audit.py

## Target Files

- scripts/conversation_work_audit.py
- src/agent_runtime/templates/project/scripts/conversation_work_audit.py
- tests/test_conversation_work_audit.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Resolve exact and slugged task filenames by canonical frontmatter ID or boundary-safe filename prefix, mirror the implementation, and test false-positive boundaries.

## Steps

1. Introduce a boundary-safe resolver for task IDs.
2. Use it from _audit_pointer while preserving current finding severity.
3. Add slugged, collision, missing, and template-parity tests.

## Acceptance Criteria

- Slugged canonical task files satisfy pointer audit.
- Prefix collisions do not satisfy pointer audit.
- Focused tests and the live audit pass.

## Verification

- `python -m pytest tests/test_conversation_work_audit.py -q`
- `python scripts/conversation_work_audit.py --check`

## Handoff

Report resolver semantics, collision coverage, and audit output.

## Stop Boundary

Stop if multiple canonical files claim the same task ID; surface the ambiguity rather than choosing one silently.
