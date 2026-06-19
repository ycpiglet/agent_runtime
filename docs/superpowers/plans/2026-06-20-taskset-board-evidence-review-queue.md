---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
work_uid: 0b3f4f40-0618-4119-b3f0-02113f97f244
kind: taskset
id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
parent_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
status: active
owner: lead_engineer
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Implement the accepted evidence_review_queue_with_progressive_disclosure_and_split_loading direction, then run exploratory beta/UX verification.
---

# Taskset Board Evidence Review Queue

## Goal

- Implement the accepted evidence_review_queue_with_progressive_disclosure_and_split_loading direction, then run exploratory beta/UX verification.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-619` | Implement Taskset Board evidence review queue and split loading states |
| `TASK-AR-620` | Run Taskset Board evidence review queue beta and UX evaluation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-619-001` | `TASK-AR-619` | Derive evidence review queue schema from Taskset Board state |
| `UNIT-TASK-AR-619-002` | `TASK-AR-619` | Render evidence queue assets and split-loading UI states |
| `UNIT-TASK-AR-620-001` | `TASK-AR-620` | Record evidence review queue beta and UX evidence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
