---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
work_uid: 1d755121-7b39-4469-b1d0-e9cabf2fe59e
kind: taskset
id: TASKSET-AR-RELEASE-CADENCE-QUERY-RECOVERY
parent_id: INIT-AR-RELEASE-CADENCE-QUERY-RECOVERY
initiative_id: INIT-AR-RELEASE-CADENCE-QUERY-RECOVERY
status: active
owner: lead-engineer
created_at: 2026-07-23T01:16:34+09:00
updated_at: 2026-07-23T01:16:34+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md
created_by: codex-root-planner
summary: Harden the cadence query boundary and prove release-auto fails loud on exhausted transient queries while preserving genuine no-tag behavior.
---

# Release Cadence Query Recovery

## Goal

- Harden the cadence query boundary and prove release-auto fails loud on exhausted transient queries while preserving genuine no-tag behavior.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-613` | Recover transient non-zero cadence queries without false not-triggered |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-613-001` | `TASK-AR-613` | Classify and retry unexpected non-zero cadence queries |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
