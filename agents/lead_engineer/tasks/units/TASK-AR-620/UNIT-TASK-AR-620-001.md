---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-620-001
work_uid: b9addb14-23c9-44af-a9a9-96473389cbf8
kind: unit
parent_id: TASK-AR-620
unit_id: UNIT-TASK-AR-620-001
task_id: TASK-AR-620
task_set_id: TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
initiative_id: INIT-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-07-23T11:20:00+09:00
updated_at: 2026-07-23T11:38:00+09:00
started_at: 2026-07-23T11:20:20+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md
created_by: codex-root-planner
summary: Add cadence isolation tasksets to the exact expected set
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - repeated_failure
context: "\u001eagent-runtime-work-scalar-v1:PR #336 run 29973935786 attempt 1 had exactly one failure after 2193 passes: the real-backlog classifier returned the newly registered cadence injection taskset as an extra item. Registering this recovery taskset creates one additional canonical ID that must be included in the same exact expectation."
inputs:
  - reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md
  - GitHub Actions run 29973935786
  - tests/test_backlog_board_tasksets.py
  - agents/project/work-items/TASKSET-DEFINITIONS.json
target_files:
  - tests/test_backlog_board_tasksets.py
scope: Add exactly the cadence injection and cadence isolation backlog recovery taskset IDs to the expected set. Do not change assertion type, classifier code, fixtures, or other IDs.
acceptance:
  - The real-backlog exact set equals the canonical registered taskset set.
  - The diff contains two additive string literals and no assertion weakening.
  - All focused tests and gates pass.
verification:
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
handoff: Report the CI failure evidence, two-ID additive diff, exact-set preservation, focused results, independent W4b, and matrix results.
stop_condition: Stop if recovery requires classifier behavior changes or any assertion weakening.
verified_at: 2026-07-23T11:22:51+09:00
verified_by: codex-root-task-ar-620
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-620-001-20260723112251.json
resolution: done
completed_at: 2026-07-23T11:38:00+09:00
closed_by: /root/task-ar-620
actual_hours: 0.35
actual_tokens: 3500
---

# UNIT-TASK-AR-620-001 - Add cadence isolation tasksets to the exact expected set

## Context

PR #336 run 29973935786 attempt 1 had exactly one failure after 2193 passes: the real-backlog classifier returned the newly registered cadence injection taskset as an extra item. Registering this recovery taskset creates one additional canonical ID that must be included in the same exact expectation.

## Inputs

- reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md
- GitHub Actions run 29973935786
- tests/test_backlog_board_tasksets.py
- agents/project/work-items/TASKSET-DEFINITIONS.json

## Target Files

- tests/test_backlog_board_tasksets.py

## Scope

Add exactly the cadence injection and cadence isolation backlog recovery taskset IDs to the expected set. Do not change assertion type, classifier code, fixtures, or other IDs.

## Steps

1. Reproduce the two missing IDs against the newly registered real backlog.
2. Add both IDs to the exact expected set in canonical ordering.
3. Run focused backlog tests and taskset gates.
4. Obtain independent W4b and the full PR matrix before integration.

## Acceptance Criteria

- The real-backlog exact set equals the canonical registered taskset set.
- The diff contains two additive string literals and no assertion weakening.
- All focused tests and gates pass.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report the CI failure evidence, two-ID additive diff, exact-set preservation, focused results, independent W4b, and matrix results.

## Stop Boundary

Stop if recovery requires classifier behavior changes or any assertion weakening.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T11:38:00+09:00`
- Resolution: `done`
- Actual hours: `0.35`
- Actual tokens: `3500`
- Closed by: `/root/task-ar-620`
- Evidence:
  - `reviews/VERIFY-2026-07-23-unit-task-ar-620-001-20260723112251.json`
<!-- work-close:end -->
