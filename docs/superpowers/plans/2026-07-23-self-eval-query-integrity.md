---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
work_uid: 8628cd1b-f1f5-44ec-8c96-6ab49334cdf4
kind: taskset
id: TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
parent_id: INIT-AR-SELF-EVAL-QUERY-INTEGRITY
initiative_id: INIT-AR-SELF-EVAL-QUERY-INTEGRITY
status: active
owner: lead-engineer
created_at: 2026-07-23T02:23:56+09:00
updated_at: 2026-07-23T02:23:56+09:00
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md
created_by: codex-root-planner
summary: Make self-eval fail loud and preserve structured evidence whenever its shared Git queries exhaust retries.
---

# Self-Eval Query Integrity

## Goal

- Make self-eval fail loud and preserve structured evidence whenever its shared Git queries exhaust retries.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-614` | Reject partial self-eval metrics after exhausted Git queries |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-614-001` | `TASK-AR-614` | Propagate shared Git query errors through self-eval |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
