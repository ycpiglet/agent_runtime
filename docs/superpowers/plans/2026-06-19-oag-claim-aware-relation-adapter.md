---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
work_uid: 525ed636-0ed2-4b53-a87d-2b124e9a8ba6
kind: taskset
id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
parent_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
initiative_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
status: active
owner: lead_engineer
created_at: 2026-06-19T12:26:00+09:00
updated_at: 2026-06-19T12:26:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Promote or replace the view-local relation summary adapter so Operator Attention Graph claim path and command readiness reflect active, expired, interrupted, and guarded claim states, then rerun beta/UX evaluation.
---

# Claim-Aware Relation Adapter

## Goal

- Promote or replace the view-local relation summary adapter so Operator Attention Graph claim path and command readiness reflect active, expired, interrupted, and guarded claim states, then rerun beta/UX evaluation.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-605` | Implement claim-aware operator relation adapter |
| `TASK-AR-606` | Run claim-aware relation adapter beta and UX evaluation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-605-001` | `TASK-AR-605` | Add claim-aware relation state mapping |
| `UNIT-TASK-AR-606-001` | `TASK-AR-606` | Record claim-aware adapter beta and UX evidence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
