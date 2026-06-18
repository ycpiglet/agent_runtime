---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
work_uid: 08278c63-b996-4266-9bda-11bd95332f05
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
parent_id: INIT-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
initiative_id: INIT-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS
status: active
owner: lead_engineer
created_at: 2026-06-18T14:50:00+09:00
updated_at: 2026-06-18T14:50:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-component-patterns
created_by: codex-planner
summary: Add reusable Button/Card/Table/Modal-style component helpers and domain pattern helpers for TaskLane, ClaimCard, EvidencePanel, CommandBar, and StateMachinePanel, then wire representative console renderers to those helpers.
---

# Design System Component Patterns

## Goal

- Add reusable Button/Card/Table/Modal-style component helpers and domain pattern helpers for TaskLane, ClaimCard, EvidencePanel, CommandBar, and StateMachinePanel, then wire representative console renderers to those helpers.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-580` | Promote console components and domain patterns |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-580-001` | `TASK-AR-580` | Promote component and domain pattern helpers |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
