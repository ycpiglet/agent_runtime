---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
work_uid: 56342787-d694-4d48-92e9-9344eaf8670b
kind: taskset
id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
parent_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
initiative_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
status: active
owner: lead_engineer
created_at: 2026-06-19T18:35:00+09:00
updated_at: 2026-06-19T18:35:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-interface-designer-task-ar-611
summary: Source-mutating implementation of the accepted Taskset Board IA RFC: attention lane derivation, taskset switcher, relation detail panel, and beta/UX evidence for desktop, mobile, keyboard, reduced-motion, and recovery states.
---

# Taskset Board Attention Workspace

## Goal

- Source-mutating implementation of the accepted Taskset Board IA RFC: attention lane derivation, taskset switcher, relation detail panel, and beta/UX evidence for desktop, mobile, keyboard, reduced-motion, and recovery states.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-612` | Implement Taskset Board attention workspace assets |
| `TASK-AR-613` | Run Taskset Board attention workspace beta and UX evaluation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-612-001` | `TASK-AR-612` | Add Taskset Board attention lane schema and workspace UI |
| `UNIT-TASK-AR-613-001` | `TASK-AR-613` | Record Taskset Board attention workspace beta and UX evidence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
