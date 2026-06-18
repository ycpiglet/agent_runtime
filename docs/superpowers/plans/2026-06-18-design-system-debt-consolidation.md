---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
work_uid: f8104307-9826-4304-9380-80f527dd3da7
kind: taskset
id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
parent_id: INIT-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
initiative_id: INIT-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION
status: active
owner: lead-engineer
created_at: 2026-06-18T18:43:04+09:00
updated_at: 2026-06-18T18:43:04+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-design-system-followups
created_by: lead-engineer
summary: Consolidate transitional spacing/radius px-alias tokens into a designed semantic scale, and promote remaining view-specific JS renderers into stable pattern modules, without re-introducing raw literals.
---

# Design System Debt Consolidation

## Goal

- Consolidate transitional spacing/radius px-alias tokens into a designed semantic scale, and promote remaining view-specific JS renderers into stable pattern modules, without re-introducing raw literals.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-583` | Consolidate transitional px-alias tokens into a semantic scale |
| `TASK-AR-584` | Promote remaining view-specific JS renderers into pattern modules |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
