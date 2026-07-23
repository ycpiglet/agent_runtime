---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-619-001
work_uid: 0ca92984-84c7-4f88-b1f7-05ea20e4f861
kind: unit
parent_id: TASK-AR-619
unit_id: UNIT-TASK-AR-619-001
task_id: TASK-AR-619
task_set_id: TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
initiative_id: INIT-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-07-23T10:15:00+09:00
updated_at: 2026-07-23T10:15:00+09:00
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md
created_by: codex-root-planner
summary: Make cadence failure injection query-complete and hermetic
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - reliability
  - repeated_failure
context: Main CI runs 29970171133 and 29970914790 each failed a different query-injection test with zero injected calls, while unchanged retries passed or were rerun. Both helpers isolate mutable module facades but delegate non-target Git queries to subprocess.run, so an unrelated runner transient can prevent the target query from being reached.
inputs:
  - reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md
  - GitHub Actions runs 29970171133 and 29970914790
  - tests/test_release_cadence_trigger.py
  - tests/test_release_auto_noncritical.py
  - scripts/release_cadence_trigger.py
target_files:
  - tests/test_release_cadence_trigger.py
  - tests/test_release_auto_noncritical.py
scope: Add or share deterministic cadence-query answer helpers in the two focused test modules, route all non-selected queries through those helpers, and keep selected-query failure counts plus report semantics unchanged.
acceptance:
  - No non-target cadence query invokes a real Git process in either affected injection family.
  - Each parameterized selected query records exactly three failures and both diff queries record exactly six failures.
  - Cadence and release-auto return structured git-query-error evidence with no mutation.
  - No production files change.
verification:
  - python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q
  - python -m pytest tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires -q --count=20
  - python scripts/taskset_work_gate.py --check
handoff: Report the failure-first guard, deterministic query matrix, exact injected call counts, repeated focused results, full matrix, and independent W4b evidence.
stop_condition: Stop if isolation requires production behavior changes, relaxed assertions, or a global pytest retry.
---

# UNIT-TASK-AR-619-001 - Make cadence failure injection query-complete and hermetic

## Context

Main CI runs 29970171133 and 29970914790 each failed a different query-injection test with zero injected calls, while unchanged retries passed or were rerun. Both helpers isolate mutable module facades but delegate non-target Git queries to subprocess.run, so an unrelated runner transient can prevent the target query from being reached.

## Inputs

- reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md
- GitHub Actions runs 29970171133 and 29970914790
- tests/test_release_cadence_trigger.py
- tests/test_release_auto_noncritical.py
- scripts/release_cadence_trigger.py

## Target Files

- tests/test_release_cadence_trigger.py
- tests/test_release_auto_noncritical.py

## Scope

Add or share deterministic cadence-query answer helpers in the two focused test modules, route all non-selected queries through those helpers, and keep selected-query failure counts plus report semantics unchanged.

## Steps

1. Add a failure-first guard proving the injected cadence path does not delegate non-target queries to real subprocess.run.
2. Model deterministic answers for baseline tag, subjects, commit count, tag time, breaking messages, and diff queries.
3. Use the deterministic responder in both partial-query injection families without altering production code.
4. Run repeated focused probes, focused files, taskset gates, independent W4b review, and the full matrix.

## Acceptance Criteria

- No non-target cadence query invokes a real Git process in either affected injection family.
- Each parameterized selected query records exactly three failures and both diff queries record exactly six failures.
- Cadence and release-auto return structured git-query-error evidence with no mutation.
- No production files change.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q`
- `python -m pytest tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires -q --count=20`
- `python scripts/taskset_work_gate.py --check`

## Handoff

Report the failure-first guard, deterministic query matrix, exact injected call counts, repeated focused results, full matrix, and independent W4b evidence.

## Stop Boundary

Stop if isolation requires production behavior changes, relaxed assertions, or a global pytest retry.
