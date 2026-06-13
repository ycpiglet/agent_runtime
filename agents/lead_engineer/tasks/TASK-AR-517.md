---
id: TASK-AR-517
display_id: TASK-AR-517
task_uid: da2e7699-1f76-4156-8eeb-82bc543fba34
registered_at: 2026-06-12T23:33:00+09:00
created_at: 2026-06-12T23:33:00+09:00
updated_at: 2026-06-13T11:50:00+09:00
started_at: 2026-06-13T02:45:16+09:00
completed_at: 2026-06-13T11:50:00+09:00
title: Work query stats export and saved views
status: completed
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - analytics
  - data_export
tags:
  - stats
  - query
  - export
  - saved-views
---

# Work query stats export and saved views

## Goal
- Turn Work Item metadata into queryable statistics, JSON/CSV export, and reusable saved views for Owner analysis.

## Context

- Recent `work stats` work introduced deterministic metadata statistics, but
  the broader query/export/saved-view layer is not complete.
- Owner wants to manipulate data, sort/filter/group it, and derive operational
  insight.

## Scope

- Extend work stats/query to support stable dimensions and metrics:
  team, role, instance, model tier, origin, component, status, lead time,
  rework, gate failures, actual tokens/hours/cost.
- Add JSON/CSV export and saved view definitions.
- Ensure invalid derived metrics such as manually stored progress are rejected
  unless computed by the tool.
- Share query primitives with Work Explorer where possible.

## Out Of Scope

- External BI integration beyond export files.
- Agent stats UI if attribution fields are not yet enforced.

## Acceptance Criteria

- Saved views can reproduce a query without rewriting CLI arguments.
- CSV/JSON export includes enough metadata to analyze outside the repo.
- Tests cover filtering, grouping, computed metrics, and invalid metrics.

## Evidence Targets

- Work query/stats tests.
- Example saved views.
- Export fixture and Owner review.

## Completion Evidence

- PR #70 (2ba5b02): work.py stats dimensions/metrics/filters/export + view save/run/list with WORK-VIEWS.json (4 seeded views); 14 tests.

## Verification Results

- pytest tests/test_work_stats.py -q -> 14 passed
- work_schema_gate --items --check -> pass
- pytest tests -q -> 587 passed (+1 pre-existing)
- W4b inst-w4b-ar517-verifier -> APPROVE
