---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
work_uid: 712b59fc-9670-4fa6-81c1-c8a2c1567db6
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION
parent_id: INIT-AR-DESIGN-SYSTEM-ASSETIZATION
initiative_id: INIT-AR-DESIGN-SYSTEM-ASSETIZATION
status: active
owner: lead_engineer
created_at: 2026-06-18T13:20:00+09:00
updated_at: 2026-06-18T13:20:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-assetization
created_by: codex-planner
summary: Move the first reusable UI primitives and domain patterns out of ui_console.py, add token scale assets, and tighten the design-system gate so existing baseline debt is tracked without blocking safe incremental refactors.
---

# Design System Assetization

## Goal

- Move the first reusable UI primitives and domain patterns out of ui_console.py, add token scale assets, and tighten the design-system gate so existing baseline debt is tracked without blocking safe incremental refactors.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-579` | Extract first UI asset layer from console |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-579-001` | `TASK-AR-579` | Extract token, primitive, and pattern asset bundle |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
