---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-614
display_id: TASK-AR-614
task_uid: 81421501-db98-4020-8aea-6003710b6f14
work_id: TASK-AR-614
work_uid: 81421501-db98-4020-8aea-6003710b6f14
kind: task
parent_id: TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
registered_at: 2026-07-23T02:23:56+09:00
created_at: 2026-07-23T02:23:56+09:00
updated_at: 2026-07-23T04:27:22+09:00
started_at: 2026-07-23T04:27:22+09:00
title: Reject partial self-eval metrics after exhausted Git queries
status: in_progress
priority: P0
difficulty: M
est_hours: 2
est_tokens: 7000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-SELF-EVAL-QUERY-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-SELF-EVAL-QUERY-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-614/UNIT-TASK-AR-614-001.md
reservation_id: RES-20260723-022356-195470fd-01
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md
created_by: codex-root-planner
summary: Surface shared Git query exhaustion as a self-eval error instead of a passing partial report.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_self_eval_metrics.py tests/test_release_cadence_trigger.py tests/test_semver_bump_property.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/taskset_work_gate.py --check
tags:
  - github-318
  - self-eval
  - git-query
  - data-integrity
---

# TASK-AR-614 - Reject partial self-eval metrics after exhausted Git queries

## Goal

- Close GitHub issue 318 by preventing self-eval from converting exhausted Git queries into passing zero or empty metrics.

## Scope

- Change only self-eval query lifecycle/error propagation and focused regressions. Preserve fixed-metric formulas, WORK-SCHEMA collection, cadence policy, and non-mutating behavior.

## Acceptance Criteria

- Every exhausted direct Git query invalidates the aggregate self-eval report regardless of other collected metrics.
- The report preserves sanitized structured git_query_errors and does not label partial Git-derived values as collected.
- Successful and deterministic no-baseline fixtures preserve their current semantics.
- Self-eval, cadence, semantic-version, host-lock, and taskset gates pass.

## Verification

- `python -m pytest tests/test_self_eval_metrics.py tests/test_release_cadence_trigger.py tests/test_semver_bump_property.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/taskset_work_gate.py --check`
