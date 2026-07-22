---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-615-001
work_uid: 74a1e5f3-6921-4b51-b606-b108a312f40c
kind: unit
parent_id: TASK-AR-615
unit_id: UNIT-TASK-AR-615-001
task_id: TASK-AR-615
task_set_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-HEAD-RECOVERY
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-07-23T03:09:36+09:00
updated_at: 2026-07-23T04:15:08+09:00
started_at: 2026-07-23T03:25:49+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md
created_by: codex-root-planner
summary: Bound retry for transient release-auto fixture commits
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - data_integrity
context: Main run 29945156772 job 89008561485 failed after 36 successful fixture commits when the next git commit returned rc 128 fatal: could not parse HEAD. The immediately preceding PR CI passed on identical product code. The fixture helper emits sanitized evidence but currently has no retry classification.
inputs:
  - reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md
  - GitHub issue 320
  - GitHub Actions run 29945156772 job 89008561485
  - tests/test_release_auto_noncritical.py
target_files:
  - tests/test_release_auto_noncritical.py
scope: Add failure-first helper coverage, classify only the exact pre-commit HEAD parse transient, retry it with a short fixed bound, and retain immediate sanitized assertions for every other failure.
acceptance:
  - The observed transient followed by success returns normally after two total attempts.
  - Three observed transients fail loud and report the final sanitized diagnostic.
  - An unrelated rc 128 failure is attempted once only.
  - No production file changes and all registered verification commands pass.
verification:
  - python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
handoff: Report first-attempt CI evidence, failure-first result, classification boundary, attempt counts, sanitization, full regressions, and independent W4b.
stop_condition: Stop if recovery requires retrying ambiguous mutations, changing production Git behavior, or weakening a CI/release gate.
verified_at: 2026-07-23T03:44:05+09:00
verified_by: codex-root-task-ar-615
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-615-001-20260723034405.json
resolution: done
completed_at: 2026-07-23T04:15:08+09:00
closed_by: codex-root-task-ar-615
actual_hours: 1.1
actual_tokens: 30000
---

# UNIT-TASK-AR-615-001 - Bound retry for transient release-auto fixture commits

## Context

Main run 29945156772 job 89008561485 failed after 36 successful fixture commits when the next git commit returned rc 128 fatal: could not parse HEAD. The immediately preceding PR CI passed on identical product code. The fixture helper emits sanitized evidence but currently has no retry classification.

## Inputs

- reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md
- GitHub issue 320
- GitHub Actions run 29945156772 job 89008561485
- tests/test_release_auto_noncritical.py

## Target Files

- tests/test_release_auto_noncritical.py

## Scope

Add failure-first helper coverage, classify only the exact pre-commit HEAD parse transient, retry it with a short fixed bound, and retain immediate sanitized assertions for every other failure.

## Steps

1. Reproduce the helper raising on one could-not-parse-HEAD result followed by a successful subprocess result.
2. Add a narrow transient classifier and bounded retry loop without changing the existing diagnostic sanitizer.
3. Prove recovery, exhaustion, unknown-error single-attempt behavior, and exact attempt counts.
4. Run full cadence/release-auto tests, taskset expectation tests, and independent W4b.

## Acceptance Criteria

- The observed transient followed by success returns normally after two total attempts.
- Three observed transients fail loud and report the final sanitized diagnostic.
- An unrelated rc 128 failure is attempted once only.
- No production file changes and all registered verification commands pass.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q`
- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report first-attempt CI evidence, failure-first result, classification boundary, attempt counts, sanitization, full regressions, and independent W4b.

## Stop Boundary

Stop if recovery requires retrying ambiguous mutations, changing production Git behavior, or weakening a CI/release gate.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T04:15:08+09:00`
- Resolution: `done`
- Actual hours: `1.1`
- Actual tokens: `30000`
- Closed by: `codex-root-task-ar-615`
- Evidence:
  - `reviews/VERIFY-2026-07-23-unit-task-ar-615-001-20260723034405.json`
<!-- work-close:end -->
