---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
work_uid: 82806fa9-1b06-4987-94f5-06d4894c6a67
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT
parent_id: INIT-AR-DESIGN-SYSTEM-TOKEN-DEBT
initiative_id: INIT-AR-DESIGN-SYSTEM-TOKEN-DEBT
status: active
owner: lead_engineer
created_at: 2026-06-18T15:20:00+09:00
updated_at: 2026-06-18T15:20:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-token-debt
created_by: codex-planner
summary: Replace console typography, spacing, and radius CSS literals with token references, remove the remaining raw color literal, and make the design-system full audit prove that literal debt is no longer hidden in the console baseline.
---

# Design System Token Debt

## Goal

- Replace console typography, spacing, and radius CSS literals with token references, remove the remaining raw color literal, and make the design-system full audit prove that literal debt is no longer hidden in the console baseline.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-581` | Tokenize console typography spacing and radius literals |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-581-001` | `TASK-AR-581` | Tokenize console CSS literal debt |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
