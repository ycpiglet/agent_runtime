---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-OWNER-REPORT-CLARITY-20261102
work_uid: 879c67e9-fcd1-419a-b267-7cab013ece9e
kind: taskset
id: TASKSET-OWNER-REPORT-CLARITY-20261102
parent_id: INIT-OWNER-REPORT-CLARITY-20261102
initiative_id: INIT-OWNER-REPORT-CLARITY-20261102
status: active
owner: lead_engineer
created_at: 2026-11-02T10:29:43+09:00
updated_at: 2026-11-02T10:29:43+09:00
origin_type: owner_request
origin_ref: owner-request:2026-11-02:compact-report-readability
created_by: codex-owner-report-planner
summary: Compact report layout, validation and reusable host guidance.
---

# Owner report clarity

## Goal

- Compact report layout, validation and reusable host guidance.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-661` | Compact report contract and generator |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-661-001` | `TASK-AR-661` | Compact owner report generation and validation |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
