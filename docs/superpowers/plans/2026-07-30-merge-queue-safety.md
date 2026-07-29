---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-MERGE-QUEUE-SAFETY
work_uid: b40a7853-9937-4707-86e7-d42a837f80bc
kind: taskset
id: TASKSET-AR-MERGE-QUEUE-SAFETY
parent_id: INIT-AR-PARALLEL-INTEGRATION-INTEGRITY
initiative_id: INIT-AR-PARALLEL-INTEGRATION-INTEGRITY
status: active
owner: lead_engineer
created_at: 2026-07-30T07:45:00+09:00
updated_at: 2026-07-30T07:45:00+09:00
origin_type: owner_request
origin_ref: conversation:2026-07-30-parallel-union-harness
created_by: codex-root
summary: Make the serial integration queue safe across processes and explicit about dependency order.
---

# Merge Queue Safety

## Goal

- Make the serial integration queue safe across processes and explicit about dependency order.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-653` | Harden merge queue concurrency and dependency ordering |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-653-001` | `TASK-AR-653` | Add repository-common lock, atomic state, and dependency-aware processing |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
