---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-616-001
work_uid: 626db422-7baa-4144-9843-61e891cafafa
kind: unit
parent_id: TASK-AR-616
unit_id: UNIT-TASK-AR-616-001
task_id: TASK-AR-616
task_set_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead_engineer
created_at: 2026-07-23T05:01:18+09:00
updated_at: 2026-07-23T05:36:47+09:00
started_at: 2026-07-23T05:14:06+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md
created_by: codex-root-planner
summary: Harden the bounded fixture commit recovery window
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - data_integrity
  - repeated_failure
context: Main run 29953104959 reproduced the exact tick-36 HEAD parse transient but exhausted TASK-AR-615's three attempts (0.15 seconds total delay). The immediately preceding PR run passed identical product code.
inputs:
  - reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md
  - reviews/W4B-2026-07-23-TASK-AR-615.md
  - GitHub issue 320
  - GitHub Actions run 29953104959
  - tests/test_release_auto_noncritical.py
target_files:
  - tests/test_release_auto_noncritical.py
  - tests/test_backlog_board_tasksets.py
scope: Add failure-first coverage for three exact pre-commit failures followed by success, extend only the capped fixture retry schedule, and verify real-commit non-duplication and permanent-failure exhaustion.
acceptance:
  - Three recognized failures followed by success return normally after four total attempts.
  - Permanent recognized failure stops at the new configured maximum with exact delay/attempt evidence.
  - Ambiguous and unrelated results never receive an extra retry beyond the already-recognized prefix.
  - The real target commit appears once and all registered verification commands pass.
verification:
  - python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
handoff: Report the CI recurrence, failure-first fourth-attempt case, capped delay schedule, exact-classifier parity, real-commit delta, full regressions, and independent W4b.
stop_condition: Stop before broadening the retry classifier, retrying ambiguous mutations, changing product Git operations, or weakening CI/release gates.
verified_at: 2026-07-23T05:36:47+09:00
verified_by: codex-root-task-ar-616
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-616-001-20260723053647.json
---

# UNIT-TASK-AR-616-001 - Harden the bounded fixture commit recovery window

## Context

Main run 29953104959 reproduced the exact tick-36 HEAD parse transient but exhausted TASK-AR-615's three attempts (0.15 seconds total delay). The immediately preceding PR run passed identical product code.

## Inputs

- reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md
- reviews/W4B-2026-07-23-TASK-AR-615.md
- GitHub issue 320
- GitHub Actions run 29953104959
- tests/test_release_auto_noncritical.py

## Target Files

- tests/test_release_auto_noncritical.py
- tests/test_backlog_board_tasksets.py

## Scope

Add failure-first coverage for three exact pre-commit failures followed by success, extend only the capped fixture retry schedule, and verify real-commit non-duplication and permanent-failure exhaustion.

## Steps

1. Reproduce three recognized failures followed by success raising at the current bound.
2. Extend the capped attempt/backoff schedule without changing the exact retry classifier.
3. Prove fourth-attempt recovery, permanent exhaustion, mixed/ambiguous fail-closed behavior, and real fixture commit delta one.
4. Run full cadence/release-auto tests, backlog taskset expectations, gates, independent W4b, and first-attempt PR/main CI.

## Acceptance Criteria

- Three recognized failures followed by success return normally after four total attempts.
- Permanent recognized failure stops at the new configured maximum with exact delay/attempt evidence.
- Ambiguous and unrelated results never receive an extra retry beyond the already-recognized prefix.
- The real target commit appears once and all registered verification commands pass.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q`
- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report the CI recurrence, failure-first fourth-attempt case, capped delay schedule, exact-classifier parity, real-commit delta, full regressions, and independent W4b.

## Stop Boundary

Stop before broadening the retry classifier, retrying ambiguous mutations, changing product Git operations, or weakening CI/release gates.