---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
work_uid: 092837f3-fa15-4468-9a2a-d5dbbf5a13c2
kind: taskset
id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
parent_id: INIT-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
initiative_id: INIT-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
status: active
owner: lead-engineer
created_at: 2026-07-23T14:08:00+09:00
updated_at: 2026-07-23T14:08:00+09:00
origin_type: runtime_bug
origin_ref: reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md
created_by: codex-root-planner
summary: Define and enforce a cross-platform execution contract for work.py verify.
---

# Work Verify Windows Shell Integrity

## Goal

- Define and enforce a cross-platform execution contract for work.py verify.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-621` | Preserve work-verify command arguments on Windows |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-621-001` | `TASK-AR-621` | Define and test cross-platform verification execution |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
