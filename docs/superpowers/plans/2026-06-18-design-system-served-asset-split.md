---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
work_uid: 796015d0-415b-4237-a35d-3d839a6d92c0
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
parent_id: INIT-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
initiative_id: INIT-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT
status: active
owner: lead_engineer
created_at: 2026-06-18T15:55:00+09:00
updated_at: 2026-06-18T15:55:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-served-asset-split
created_by: codex-planner
summary: Physically separate the console's served HTML/CSS/JS string assets from the Python API/server module while preserving /, /app.css, and /app.js behavior.
---

# Design System Served Asset Split

## Goal

- Physically separate the console's served HTML/CSS/JS string assets from the Python API/server module while preserving /, /app.css, and /app.js behavior.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-582` | Split console served asset strings |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-582-001` | `TASK-AR-582` | Move served HTML CSS JS assets out of ui_console |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
