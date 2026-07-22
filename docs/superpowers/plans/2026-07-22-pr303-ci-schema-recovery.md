---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-PR303-CI-SCHEMA-RECOVERY
work_uid: 6641809e-0d41-4e47-b15b-f7e26f9b184e
kind: taskset
id: TASKSET-AR-PR303-CI-SCHEMA-RECOVERY
parent_id: INIT-AR-PR303-CI-SCHEMA-RECOVERY
initiative_id: INIT-AR-PR303-CI-SCHEMA-RECOVERY
status: active
owner: lead-engineer
created_at: 2026-07-22T18:26:18+09:00
updated_at: 2026-07-22T18:26:18+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md
created_by: codex-root-planner
summary: Normalize the legacy TASK-AR-594 evidence reference into the canonical work-item schema.
---

# CI Schema Recovery

## Goal

- Normalize the legacy TASK-AR-594 evidence reference into the canonical work-item schema.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-610` | Normalize legacy failed verification evidence references |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-610-001` | `TASK-AR-610` | Fold the legacy failure link into canonical evidence refs |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
