---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-596
display_id: TASK-AR-596
task_uid: 5f9cdb53-3730-4788-be19-d6344ba48928
work_id: TASK-AR-596
work_uid: 5f9cdb53-3730-4788-be19-d6344ba48928
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
started_at: 2026-07-19T11:55:48+09:00
updated_at: 2026-07-19T12:07:13+09:00
title: Resolve slugged canonical task files in conversation audit
status: completed
priority: P1
difficulty: S
est_hours: 2
est_tokens: 4500
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
reservation_id: RES-20260719-102806-bbbc9438-03
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:
created_by: codex-root-planner
summary: Replace exact short-filename assumptions with ID-aware task record resolution.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python -m pytest tests/test_conversation_work_audit.py -q
  - python scripts/conversation_work_audit.py --check
verification_status: passed
verified_at: 2026-07-19T12:03:59+09:00
verified_by: codex-root-task-ar-596
evidence_refs:
  - reviews/VERIFY-2026-07-19-task-ar-596-20260719120359.json
review_evidence_refs:
  - reviews/W4B-2026-07-19-TASK-AR-596.md
  - reviews/ROLE-REVIEW-2026-07-19-TASK-AR-596-INDEPENDENT-AUDITOR.md
implementation_commit: 1abfe76
resolution: done
completed_at: 2026-07-19T12:07:13+09:00
closed_by: codex-root-task-ar-596
actual_hours: 0.2
actual_tokens: 5000
---

# TASK-AR-596 - Resolve slugged canonical task files in conversation audit

## Goal

- Resolve GitHub #290 so active pointers find canonical TASK files with descriptive slug suffixes.

## Scope

- Update live/template conversation audit and focused tests; preserve warning behavior for genuinely missing or ambiguous records.

## Acceptance Criteria

- A pointer to TASK-231 resolves TASK-231-taskset-dispatcher-selection-order.md.
- TASK-231 does not accidentally resolve TASK-2310 or an unrelated malformed record.
- Missing and ambiguous records remain visible as findings.

## Verification

- `python -m pytest tests/test_conversation_work_audit.py -q`
- `python scripts/conversation_work_audit.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-19T12:07:13+09:00`
- Resolution: `done`
- Actual hours: `0.2`
- Actual tokens: `5000`
- Closed by: `codex-root-task-ar-596`
- Evidence:
  - `reviews/VERIFY-2026-07-19-task-ar-596-20260719120359.json`
<!-- work-close:end -->
