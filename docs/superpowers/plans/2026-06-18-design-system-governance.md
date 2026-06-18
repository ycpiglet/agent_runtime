---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
work_uid: bdea175e-95ae-4af7-a8c7-8c8a51260440
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
parent_id: INIT-AR-DESIGN-SYSTEM-GOVERNANCE
initiative_id: INIT-AR-DESIGN-SYSTEM-GOVERNANCE
status: active
owner: lead_engineer
created_at: 2026-06-18T12:51:06+09:00
updated_at: 2026-06-18T12:51:06+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-governance
created_by: codex-planner
summary: Publish a design-system operating contract, assetization classification workflow, UI/UX role split, and deterministic gate so new UI work can reuse components while still proposing new design directions.
---

# Design System Governance

## Goal

- Publish a design-system operating contract, assetization classification workflow, UI/UX role split, and deterministic gate so new UI work can reuse components while still proposing new design directions.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-578` | Publish design-system governance and gate |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-578-001` | `TASK-AR-578` | Publish design-system governance and gate |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
