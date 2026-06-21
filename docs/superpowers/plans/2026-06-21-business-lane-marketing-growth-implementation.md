---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
work_uid: b54fee04-dc08-4008-bca6-77004694e008
kind: taskset
id: TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
parent_id: INIT-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION
status: active
owner: lead_engineer
created_at: 2026-06-21T19:00:00+09:00
updated_at: 2026-06-21T19:00:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Publish a draft campaign-readiness packet and decision triggers from the marketing-growth lane contract.
---

# Business Lanes Marketing Growth Implementation

## Goal

- Publish a draft campaign-readiness packet and decision triggers from the marketing-growth lane contract.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-596` | Create marketing campaign-readiness evidence packet for owner review |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-596-001` | `TASK-AR-596` | Draft marketing growth campaign-readiness packet |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
