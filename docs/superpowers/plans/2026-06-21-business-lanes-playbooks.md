---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-LANE-PLAYBOOKS
work_uid: 2eed3f8e-214d-4fb7-83ed-9aee8f3cdaee
kind: taskset
id: TASKSET-AR-BUSINESS-LANE-PLAYBOOKS
parent_id: INIT-AR-BUSINESS-LANES
initiative_id: INIT-AR-BUSINESS-LANES
status: active
owner: lead_engineer
created_at: 2026-06-21T17:45:39+09:00
updated_at: 2026-06-21T17:45:39+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Create lane-specific operating packets that convert the business operating system into directly executable finance, marketing, sales, operations, support, planning, and strategy workflows.
---

# Business Lanes Playbooks

## Goal

- Create lane-specific operating packets that convert the business operating system into directly executable finance, marketing, sales, operations, support, planning, and strategy workflows.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-594` | Publish lane playbooks for durable business execution |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-594-001` | `TASK-AR-594` | Draft and mirror business lane playbook packet |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
