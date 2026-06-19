---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
work_uid: 62aaf5d1-34ca-45c9-9ac3-6a2b50b5582a
kind: taskset
id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
parent_id: INIT-AR-TSAW-CLAIM-EMPTY-REFINEMENT
initiative_id: INIT-AR-TSAW-CLAIM-EMPTY-REFINEMENT
status: active
owner: lead_engineer
created_at: 2026-06-19T21:56:00+09:00
updated_at: 2026-06-19T21:56:00+09:00
origin_type: beta_finding
origin_ref: reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
created_by: codex-ux-evaluator-ar-613
summary: Make the Taskset Board attention workspace surface live active claims and clarify zero-count lane recovery copy, then rerun beta/UX evidence.
---

# TSAW Claim And Empty State Refinement

## Goal

- Make the Taskset Board attention workspace surface live active claims and clarify zero-count lane recovery copy, then rerun beta/UX evidence.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-614` | Fix Taskset attention active-claim freshness and empty lane copy |
| `TASK-AR-615` | Rerun Taskset attention workspace beta after claim and empty-state refinement |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-614-001` | `TASK-AR-614` | Patch attention workspace claim and empty recovery states |
| `UNIT-TASK-AR-615-001` | `TASK-AR-615` | Record refined attention workspace beta and UX evidence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
