---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
work_uid: 95358147-8acc-426b-829c-455a3c3d344c
kind: taskset
id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
parent_id: INIT-AR-BUSINESS-OPERATING-SYSTEM
initiative_id: INIT-AR-BUSINESS-OPERATING-SYSTEM
status: active
owner: lead_engineer
created_at: 2026-06-21T16:20:00+09:00
updated_at: 2026-06-21T16:20:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-operating-system-continuation
created_by: codex-planner
summary: Extend business operations beyond team registration by adding operations/support and planning/strategy lanes plus a reusable operating packet for cross-agent business cycles.
---

# Business Operating System

## Goal

- Extend business operations beyond team registration by adding operations/support and planning/strategy lanes plus a reusable operating packet for cross-agent business cycles.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-593` | Publish business operating lanes and cycle packet |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-593-001` | `TASK-AR-593` | Publish business operating lanes and cycle packet |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
