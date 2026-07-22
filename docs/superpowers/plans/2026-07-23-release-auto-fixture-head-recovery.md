---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
work_uid: f3a079a4-5258-43a8-8a1c-d4debf90cf8b
kind: taskset
id: TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
parent_id: INIT-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
status: active
owner: lead-engineer
created_at: 2026-07-23T03:09:36+09:00
updated_at: 2026-07-23T03:09:36+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md
created_by: codex-root-planner
summary: Make the release-auto test fixture resilient to a proven pre-commit HEAD parse transient without hiding deterministic Git failures.
---

# Release-Auto Fixture HEAD Recovery

## Goal

- Make the release-auto test fixture resilient to a proven pre-commit HEAD parse transient without hiding deterministic Git failures.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-615` | Retry recognized pre-commit HEAD parse transients in release-auto fixtures |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-615-001` | `TASK-AR-615` | Bound retry for transient release-auto fixture commits |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
