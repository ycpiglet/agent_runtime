---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-611-001
work_uid: 38c38190-54fd-43d7-84b8-25525512525a
kind: unit
parent_id: TASK-AR-611
unit_id: UNIT-TASK-AR-611-001
task_id: TASK-AR-611
task_set_id: TASKSET-AR-BACKLOG-TASKSET-TEST-RECOVERY
initiative_id: INIT-AR-BACKLOG-TASKSET-TEST-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-22T18:48:38+09:00
updated_at: 2026-07-22T20:03:04+09:00
origin_type: downstream_bug
origin_ref: github-actions:run-29909181630
created_by: codex-root-planner
summary: Add newly registered tasksets to the exact-set regression test
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: GitHub Actions run 29909181630 reported one failure: test_real_backlog_tasks_are_classified_into_registered_task_sets rejected two newly registered tasksets. Registering this recovery taskset adds one more legitimate ID that the same exact-set assertion must include.
inputs:
  - GitHub Actions run 29909181630 failed log
  - agents/project/work-items/TASKSET-DEFINITIONS.json
  - tests/test_backlog_board_tasksets.py
target_files:
  - tests/test_backlog_board_tasksets.py
scope: Add exactly the three newly registered taskset IDs to the expected set. No production-code changes and no weakening from exact equality to subset checks.
acceptance:
  - Exact-set assertion remains exact and passes with every currently registered taskset.
  - No file outside the test and generated governance records changes.
verification:
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python -m pytest tests -q
handoff: Provide focused/full pytest counts, exact verified HEAD, and independent W4b evidence.
stop_condition: Stop if the actual taskset registry contains any additional unplanned ID or if fixing the failure requires production classifier changes.
verified_at: 2026-07-22T19:20:21+09:00
verified_by: codex-root-task-ar-611
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-611-001-20260722192021.json
resolution: done
completed_at: 2026-07-22T20:03:04+09:00
closed_by: codex-root
actual_hours: 1.0
actual_tokens: 14000
---

# UNIT-TASK-AR-611-001 - Add newly registered tasksets to the exact-set regression test

## Context

GitHub Actions run 29909181630 reported one failure: test_real_backlog_tasks_are_classified_into_registered_task_sets rejected two newly registered tasksets. Registering this recovery taskset adds one more legitimate ID that the same exact-set assertion must include.

## Inputs

- GitHub Actions run 29909181630 failed log
- agents/project/work-items/TASKSET-DEFINITIONS.json
- tests/test_backlog_board_tasksets.py

## Target Files

- tests/test_backlog_board_tasksets.py

## Scope

Add exactly the three newly registered taskset IDs to the expected set. No production-code changes and no weakening from exact equality to subset checks.

## Steps

1. Confirm the actual extra IDs from the CI failure and taskset registry.
2. Add the three registered IDs to the exact expected set.
3. Run the focused test and full package suite.
4. Run taskset, RBAC, classifier, and Owner governance gates.

## Acceptance Criteria

- Exact-set assertion remains exact and passes with every currently registered taskset.
- No file outside the test and generated governance records changes.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python -m pytest tests -q`

## Handoff

Provide focused/full pytest counts, exact verified HEAD, and independent W4b evidence.

## Stop Boundary

Stop if the actual taskset registry contains any additional unplanned ID or if fixing the failure requires production classifier changes.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-22T20:03:04+09:00`
- Resolution: `done`
- Actual hours: `1.0`
- Actual tokens: `14000`
- Closed by: `codex-root`
- Evidence:
  - `reviews/VERIFY-2026-07-22-unit-task-ar-611-001-20260722192021.json`
<!-- work-close:end -->
