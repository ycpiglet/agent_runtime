---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-SECURITY-RESILIENCE-20261101
work_uid: 2157e062-7d44-4551-afca-efe2a1d34675
kind: taskset
id: TASKSET-AR-SECURITY-RESILIENCE-20261101
parent_id: INIT-AR-SECURITY-RESILIENCE-20261101
initiative_id: INIT-AR-SECURITY-RESILIENCE-20261101
status: active
owner: lead-engineer
created_at: 2026-11-01T01:40:41+09:00
updated_at: 2026-11-01T01:40:41+09:00
origin_type: owner_request
origin_ref: owner-request:2026-11-01-independent-security-resilience
created_by: codex-security-20261101
summary: A reusable role and bounded verification evidence contract; consumer findings remain host-owned.
---

# Security and resilience reviewer

## Goal

- A reusable role and bounded verification evidence contract; consumer findings remain host-owned.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-660` | Add independent security and resilience reviewer with evidence closure |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-660-001` | `TASK-AR-660` | Add independent security and resilience reviewer with evidence closure |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
