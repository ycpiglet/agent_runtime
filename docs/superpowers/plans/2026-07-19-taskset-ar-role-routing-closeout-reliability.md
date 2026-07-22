---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
work_uid: fd9f34b1-1639-4c63-83a7-f6402d44787f
kind: taskset
id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
parent_id: INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
initiative_id: INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
status: active
owner: lead-engineer
created_at: 2026-07-19T11:03:47+09:00
updated_at: 2026-07-19T11:03:47+09:00
origin_type: runtime_discovery
origin_ref: TASK-AR-594 closeout overlay release failure
created_by: codex-root-planner
summary: Repair the overlay claim lifecycle gap discovered while closing TASK-AR-594.
---

# Role Routing Closeout Reliability

## Goal

- Repair the overlay claim lifecycle gap discovered while closing TASK-AR-594.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-601` | Make routed review overlays cleanly releasable |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-601-001` | `TASK-AR-601` | Repair overlay lifecycle artifacts and recursion guard |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
