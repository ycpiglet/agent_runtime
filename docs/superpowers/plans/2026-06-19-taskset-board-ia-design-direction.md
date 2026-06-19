---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
work_uid: db368c14-2c00-4c00-ac12-592a6853f6a1
kind: taskset
id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
parent_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
initiative_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
status: active
owner: lead_engineer
created_at: 2026-06-19T15:36:00+09:00
updated_at: 2026-06-19T15:36:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Resolve the post-OAG UX watch that Taskset Board discovery and whole-board focus traversal are too long now that the board contains 49 tasksets; run a lead-designer IA/design seminar, publish an RFC, then derive the next implementation and beta-evaluation taskset.
---

# Taskset Board IA Design Direction

## Goal

- Resolve the post-OAG UX watch that Taskset Board discovery and whole-board focus traversal are too long now that the board contains 49 tasksets; run a lead-designer IA/design seminar, publish an RFC, then derive the next implementation and beta-evaluation taskset.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-609` | Run Taskset Board IA design seminar |
| `TASK-AR-610` | Publish Taskset Board IA design RFC |
| `TASK-AR-611` | Derive Taskset Board IA implementation and beta units |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-609-001` | `TASK-AR-609` | Run Taskset Board IA lead-designer seminar |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
