---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-HOST-REQUIRED-MERGE-GATES
work_uid: eb8ded85-f713-462a-a94d-2b7e1f86c9af
kind: taskset
id: TASKSET-AR-HOST-REQUIRED-MERGE-GATES
parent_id: INIT-AR-PROJECT-MERGE-GOVERNANCE
initiative_id: INIT-AR-PROJECT-MERGE-GOVERNANCE
status: active
owner: lead-engineer
created_at: 2026-07-30T09:20:00+09:00
updated_at: 2026-07-30T09:20:00+09:00
origin_type: owner_request
origin_ref: conversation:2026-07-30-design-gate-enforcement
created_by: codex-root
summary: Bind immutable host policy to queue entries and execute applicable required gates after rebase but before merge.
---

# Host Required Merge Gates

## Goal

- Bind immutable host policy to queue entries and execute applicable required gates after rebase but before merge.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-654` | Enforce host-owned required gates in the merge queue |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-654-001` | `TASK-AR-654` | Bind and execute host-required merge gates |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
