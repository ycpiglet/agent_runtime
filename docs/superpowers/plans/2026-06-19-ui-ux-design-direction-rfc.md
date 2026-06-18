---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
work_uid: 8fb5378d-e3d2-4d70-bc2b-06cb5ed31d9e
kind: taskset
id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
parent_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
initiative_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
status: active
owner: lead_engineer
created_at: 2026-06-19T08:18:00+09:00
updated_at: 2026-06-19T08:18:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Run the post-closeout UI/UX design-direction loop: lead-designer exploration, design-system promotion decisions, implementation refactor scope, and beta-tester evaluation criteria before mutating UI source again.
---

# UI UX Design Direction RFC

## Goal

- Run the post-closeout UI/UX design-direction loop: lead-designer exploration, design-system promotion decisions, implementation refactor scope, and beta-tester evaluation criteria before mutating UI source again.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-600` | Run lead-designer UI direction seminar |
| `TASK-AR-601` | Publish UI design direction RFC |
| `TASK-AR-602` | Derive next UI implementation and UX evaluation units |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-600-001` | `TASK-AR-600` | Run lead-designer UI direction seminar |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
