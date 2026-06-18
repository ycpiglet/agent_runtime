---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
work_uid: a48cf376-aed6-4264-b6ae-377000019975
kind: taskset
id: TASKSET-AR-BUSINESS-OPERATIONS-TEAMS
parent_id: INIT-AR-BUSINESS-OPERATIONS-TEAMS
initiative_id: INIT-AR-BUSINESS-OPERATIONS-TEAMS
status: active
owner: lead_engineer
created_at: 2026-06-17T22:10:00+09:00
updated_at: 2026-06-17T22:10:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-17-business-operations-teams
created_by: codex-planner
summary: Extend the live org overlay and host scaffold with business-side teams for monetization, asset management, marketing, and compliant sales automation.
---

# Business Operations Teams

## Goal

- Extend the live org overlay and host scaffold with business-side teams for monetization, asset management, marketing, and compliant sales automation.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-577` | Add business operations teams to org overlays |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-577-001` | `TASK-AR-577` | Publish business operations org model |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
