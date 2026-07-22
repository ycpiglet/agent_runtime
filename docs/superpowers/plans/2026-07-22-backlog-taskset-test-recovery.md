---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY
work_uid: 6499b4e7-147c-45af-987b-2b07d1562146
kind: taskset
id: TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY
parent_id: INIT-AR-BACKLOG-TASKSET-TEST-RECOVERY
initiative_id: INIT-AR-BACKLOG-TASKSET-TEST-RECOVERY
status: active
owner: lead-engineer
created_at: 2026-07-22T18:48:38+09:00
updated_at: 2026-07-22T18:48:38+09:00
origin_type: downstream_bug
origin_ref: github-actions:run-29909181630
created_by: codex-root-planner
summary: Update the canonical real-backlog taskset expectation for all newly registered tasksets and prove the full package suite remains green.
---

# Backlog Taskset Test Recovery

## Goal

- Update the canonical real-backlog taskset expectation for all newly registered tasksets and prove the full package suite remains green.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-611` | Synchronize the real-backlog taskset expectation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-611-001` | `TASK-AR-611` | Add newly registered tasksets to the exact-set regression test |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
