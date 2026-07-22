---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
work_uid: 0dbe0f60-345e-4dda-9028-6d508ae2f53b
kind: taskset
id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
parent_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
status: active
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T10:28:06+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
created_by: codex-root-planner
summary: Fix the four open host-reported defects, integrate crash recovery and allimbot notifications, synchronize project state, then cut and verify v0.7.0.
---

# Upstream Intake Closer

## Goal

- Fix the four open host-reported defects, integrate crash recovery and allimbot notifications, synchronize project state, then cut and verify v0.7.0.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-594` | Honor canonical taskset task order |
| `TASK-AR-595` | Enforce isolated build prerequisites in host updater |
| `TASK-AR-596` | Resolve slugged canonical task files in conversation audit |
| `TASK-AR-597` | Preserve Git stderr in release-auto test failures |
| `TASK-AR-598` | Integrate crash-safe session resume audit |
| `TASK-AR-599` | Adopt never-blocking allimbot notifications |
| `TASK-AR-602` | Synchronize state and release v0.7.0 |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-594-001` | `TASK-AR-594` | Implement canonical task order selection |
| `UNIT-TASK-AR-595-001` | `TASK-AR-595` | Repair updater build isolation |
| `UNIT-TASK-AR-596-001` | `TASK-AR-596` | Implement task-ID-aware pointer resolution |
| `UNIT-TASK-AR-597-001` | `TASK-AR-597` | Add diagnostic Git helper failures |
| `UNIT-TASK-AR-598-001` | `TASK-AR-598` | Rebase and verify session resume recovery |
| `UNIT-TASK-AR-599-001` | `TASK-AR-599` | Wire optional allimbot notifications end to end |
| `UNIT-TASK-AR-602-001` | `TASK-AR-602` | Close state and publish v0.7.0 |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
