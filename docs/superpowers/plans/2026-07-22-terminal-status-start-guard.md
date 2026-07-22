---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-TERMINAL-STATUS-START-GUARD
work_uid: 3ce87937-bae4-414f-9bc3-6238d1f96dab
kind: taskset
id: TASKSET-AR-TERMINAL-STATUS-START-GUARD
parent_id: INIT-AR-TERMINAL-STATUS-START-GUARD
initiative_id: INIT-AR-TERMINAL-STATUS-START-GUARD
status: active
owner: lead-engineer
created_at: 2026-07-22T21:43:00+09:00
updated_at: 2026-07-22T21:43:00+09:00
origin_type: review_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md
created_by: codex-root-planner
summary: Align taskset terminal-status selection and start transitions with the established closed/released status vocabulary.
---

# Terminal Status Start Guard

## Goal

- Align taskset terminal-status selection and start transitions with the established closed/released status vocabulary.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-612` | Block taskset restart of closed and released records |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-612-001` | `TASK-AR-612` | Treat closed and released task statuses as terminal |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
