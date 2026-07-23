---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-619
display_id: TASK-AR-619
task_uid: d1cb4ea0-ca83-497c-a938-caf541dc2f29
work_id: TASK-AR-619
work_uid: d1cb4ea0-ca83-497c-a938-caf541dc2f29
kind: task
parent_id: TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
registered_at: 2026-07-23T10:15:00+09:00
created_at: 2026-07-23T10:15:00+09:00
updated_at: 2026-07-23T11:08:46+09:00
title: Isolate cadence query-failure injection tests from real Git
status: planned
priority: P0
difficulty: S
est_hours: 1
est_tokens: 5000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-619/UNIT-TASK-AR-619-001.md
reservation_id: RES-20260723-101500-1ff230a3-01
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md
created_by: codex-root-planner
summary: Supply deterministic successful answers for every non-target cadence query during failure injection.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q
  - python -m pytest tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires -q
  - python scripts/taskset_work_gate.py --check
tags:
  - ci-flake
  - test-isolation
  - release-cadence
  - release-auto
verification_status: passed
verified_at: 2026-07-23T11:08:46+09:00
verified_by: codex-root-worker
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-619-20260723103734.json
  - reviews/VERIFY-2026-07-23-task-ar-619-20260723110846.json
---

# TASK-AR-619 - Isolate cadence query-failure injection tests from real Git

## Goal

- Prevent non-target Git process transients from producing zero-call false failures in cadence query-failure tests.

## Scope

- Change only the cadence and release-auto query-failure test harness and focused regression coverage. Preserve production behavior, retry counts, cadence thresholds, and release classification.

## Acceptance Criteria

- The cadence per-query failure matrix no longer calls real Git after its injected module is configured.
- The release-auto partial-query failure scenario no longer calls real Git for cadence answers after failure injection begins.
- Selected queries retain exact retry counts and both reports retain git-query-error semantics.
- Focused tests pass repeatedly and the full supported Python matrix passes.

## Verification

- `python -m pytest tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py -q`
- `python -m pytest tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires -q`
- `python scripts/taskset_work_gate.py --check`