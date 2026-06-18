---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
work_uid: 2e89e1a8-04e6-4184-9ce2-60af313c9381
kind: taskset
id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
parent_id: INIT-AR-UI-UX-CONTINUOUS-IMPROVEMENT
initiative_id: INIT-AR-UI-UX-CONTINUOUS-IMPROVEMENT
status: active
owner: lead_engineer
created_at: 2026-06-19T00:00:00+09:00
updated_at: 2026-06-19T00:00:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Create an automated UI/UX improvement loop: assess tokens, components, typography, size, color, motion, effects, schemas, and assets; record seminar/meeting/beta-tester review needs; then propose the next concrete UI refactor tasks for execution and verification.
---

# UI UX Cycle Automation

## Goal

- Create an automated UI/UX improvement loop: assess tokens, components, typography, size, color, motion, effects, schemas, and assets; record seminar/meeting/beta-tester review needs; then propose the next concrete UI refactor tasks for execution and verification.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-597` | Add UI/UX cycle conductor |
| `TASK-AR-598` | Wire UI/UX cycle into seminar and beta-tester artifacts |
| `TASK-AR-599` | Automate UI/UX cycle recommendations into backlog intake |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-597-001` | `TASK-AR-597` | Add UI/UX cycle conductor |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
