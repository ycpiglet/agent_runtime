---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
work_uid: 94b2bcb2-bb5f-4280-8cd2-a1c65c14a7c8
kind: taskset
id: TASKSET-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
parent_id: INIT-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-SALES-REVENUE-IMPLEMENTATION
status: active
owner: lead_engineer
created_at: 2026-06-21T19:25:00+09:00
updated_at: 2026-06-21T19:25:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Publish draft ICP/qualify/deal-readiness packet and explicit escalation guards from the sales-revenue lane contract.
---

# Business Lanes Sales Revenue Implementation

## Goal

- Publish draft ICP/qualify/deal-readiness packet and explicit escalation guards from the sales-revenue lane contract.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-597` | Create sales revenue readiness packet for owner review |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-597-001` | `TASK-AR-597` | Draft sales revenue readiness packet |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
