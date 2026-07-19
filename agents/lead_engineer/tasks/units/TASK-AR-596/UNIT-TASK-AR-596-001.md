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
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
started_at: 2026-07-19T11:55:48+09:00
updated_at: 2026-07-19T12:07:12+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Implement task-ID-aware pointer resolution
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: GitHub
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
verified_at: 2026-07-19T11:59:06+09:00
verified_by: codex-root-task-ar-596
evidence_refs:
  - reviews/VERIFY-2026-07-19-unit-task-ar-596-001-20260719115906.json
review_evidence_refs:
  - reviews/W4B-2026-07-19-TASK-AR-596.md
  - reviews/ROLE-REVIEW-2026-07-19-TASK-AR-596-INDEPENDENT-AUDITOR.md
implementation_commit: 1abfe76
resolution: done
completed_at: 2026-07-19T12:07:12+09:00
closed_by: codex-root-task-ar-596
actual_hours: 0.15
actual_tokens: 3500
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

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-19T12:07:12+09:00`
- Resolution: `done`
- Actual hours: `0.15`
- Actual tokens: `3500`
- Closed by: `codex-root-task-ar-596`
- Evidence:
  - `reviews/VERIFY-2026-07-19-unit-task-ar-596-001-20260719115906.json`
<!-- work-close:end -->
