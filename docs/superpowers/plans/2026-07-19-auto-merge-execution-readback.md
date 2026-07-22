---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
work_uid: 8f3909c9-3320-42b9-b9d6-a5ac4bd7f27a
kind: taskset
id: TASKSET-AR-AUTO-MERGE-INTEGRITY
parent_id: INIT-AR-AUTO-MERGE-INTEGRITY
initiative_id: INIT-AR-AUTO-MERGE-INTEGRITY
status: active
owner: lead_engineer
created_at: 2026-07-19T10:34:25+09:00
updated_at: 2026-07-19T10:34:25+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md
created_by: codex-root
summary: Close downstream BUG-014 with deterministic remote read-back.
---

# Merge Truth Keeper

## Goal

- Close downstream BUG-014 with deterministic remote read-back.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-600` | Confirm remote merge state before success |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-600-001` | `TASK-AR-600` | Patch auto-merge execution read-back |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
