---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
work_uid: c7481933-0f9d-41d9-97a5-31ca2ca521d8
kind: taskset
id: TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
parent_id: INIT-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
initiative_id: INIT-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
status: active
owner: lead-engineer
created_at: 2026-07-23T10:15:00+09:00
updated_at: 2026-07-23T10:15:00+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md
created_by: codex-root-planner
summary: Make cadence and release-auto failure-injection tests hermetic while preserving exact retry and fail-loud contracts.
---

# Release Cadence Injection Test Isolation

## Goal

- Make cadence and release-auto failure-injection tests hermetic while preserving exact retry and fail-loud contracts.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-619` | Isolate cadence query-failure injection tests from real Git |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-619-001` | `TASK-AR-619` | Make cadence failure injection query-complete and hermetic |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
