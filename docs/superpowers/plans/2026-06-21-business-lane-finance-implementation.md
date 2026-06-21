---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
work_uid: 213854da-f5b4-4e60-bc1e-5765a531c478
kind: taskset
id: TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
parent_id: INIT-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
initiative_id: INIT-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION
status: active
owner: lead_engineer
created_at: 2026-06-21T18:30:00+09:00
updated_at: 2026-06-21T18:30:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-21-business-lane-playbooks
created_by: codex-planner
summary: Build finance/accounting execution packets (pricing-policy assumption, cost evidence, and decision boundaries) from the playbook contract.
---

# Business Lanes Finance Implementation

## Goal

- Build finance/accounting execution packets (pricing-policy assumption, cost evidence, and decision boundaries) from the playbook contract.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-595` | Create finance policy evidence packet for execution planning |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-595-001` | `TASK-AR-595` | Draft finance policy evidence packet |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
