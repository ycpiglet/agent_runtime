---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
work_uid: 115a07f5-f2cd-480d-9048-ba2de8483524
kind: taskset
id: TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
parent_id: INIT-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
initiative_id: INIT-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
status: active
owner: lead-engineer
created_at: 2026-07-23T11:20:00+09:00
updated_at: 2026-07-23T11:20:00+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md
created_by: codex-root-planner
summary: Synchronize the exact real-backlog taskset expectation with the two new registered tasksets.
---

# Cadence Isolation Backlog Expectation Recovery

## Goal

- Synchronize the exact real-backlog taskset expectation with the two new registered tasksets.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-620` | Synchronize cadence isolation tasksets in the exact backlog expectation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-620-001` | `TASK-AR-620` | Add cadence isolation tasksets to the exact expected set |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
