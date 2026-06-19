---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
work_uid: c5f6e340-4ca5-4319-a317-d4b030ff0e5f
kind: taskset
id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
parent_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
initiative_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
status: active
owner: lead-engineer
created_at: 2026-06-20T05:18:36+09:00
updated_at: 2026-06-20T05:18:36+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-autonomous-loop
created_by: lead-engineer
summary: Wire the new visual components into every relevant live view, boot-verify the served console, fix integration gaps, and run a WCAG AA + responsive pass on the new visual system. Permissive, no-build, token-driven.
---

# Visual System Integration & Verification

## Goal

- Wire the new visual components into every relevant live view, boot-verify the served console, fix integration gaps, and run a WCAG AA + responsive pass on the new visual system. Permissive, no-build, token-driven.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-591` | Wire new visual components into live views + boot-verify the console |
| `TASK-AR-592` | Accessibility + responsive pass on the new visual system |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-591-001` | `TASK-AR-591` | Audit + wire components into live views |
| `UNIT-TASK-AR-591-002` | `TASK-AR-591` | Boot-verify the served console |
| `UNIT-TASK-AR-592-001` | `TASK-AR-592` | A11y audit + fixes for the new components |
| `UNIT-TASK-AR-592-002` | `TASK-AR-592` | Responsive pass for the new visuals |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
