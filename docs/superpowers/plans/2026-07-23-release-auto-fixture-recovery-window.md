---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
work_uid: ea7f8154-db99-4e2d-be9a-14a1c54aff4a
kind: taskset
id: TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
parent_id: INIT-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
status: active
owner: lead-engineer
created_at: 2026-07-23T05:01:18+09:00
updated_at: 2026-07-23T05:01:18+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md
created_by: codex-root-planner
summary: Extend the bounded wait for an already-recognized fixture-only Git transient without broadening mutation retries.
---

# Release-Auto Fixture Recovery Window

## Goal

- Extend the bounded wait for an already-recognized fixture-only Git transient without broadening mutation retries.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-616` | Extend the exact fixture HEAD recovery window |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-616-001` | `TASK-AR-616` | Harden the bounded fixture commit recovery window |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
