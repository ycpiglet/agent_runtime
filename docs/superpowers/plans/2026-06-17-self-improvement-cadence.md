---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
work_uid: 5180dd75-7efc-4cdd-a180-6b50061663cf
kind: taskset
id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
parent_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
status: active
owner: lead_engineer
created_at: 2026-06-17T08:31:23+09:00
updated_at: 2026-06-17T08:31:23+09:00
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Detect low-frequency roles and runtime assets, run review/retro/meeting/seminar/compound/doc-steward/scribe cycles from evidence, and publish measurable maturity signals.
---

# Self Improvement Cadence

## Goal

- Detect low-frequency roles and runtime assets, run review/retro/meeting/seminar/compound/doc-steward/scribe cycles from evidence, and publish measurable maturity signals.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-570` | Measure low-frequency role and asset usage |
| `TASK-AR-571` | Generate product-native self-improvement cycle records |
| `TASK-AR-572` | Publish maturity thresholds and improvement report |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-570-001` | `TASK-AR-570` | Build self-improvement metrics baseline |
| `UNIT-TASK-AR-571-001` | `TASK-AR-571` | Record the first self-improvement cycle |
| `UNIT-TASK-AR-572-001` | `TASK-AR-572` | Wire maturity reporting into governance surfaces |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
