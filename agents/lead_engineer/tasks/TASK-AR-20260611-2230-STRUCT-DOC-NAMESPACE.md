---
id: TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE
display_id: TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE
task_uid: 473c85d2-8152-49c1-b2d8-f14c7679b579
registered_at: 2026-06-11T22:28:32+09:00
created_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
title: Evidence namespace and project config/release split plan
status: planned
priority: P2
difficulty: M
est_hours: 5
est_tokens: 3500
owner: lead_engineer
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - structure
  - evidence
  - docs
  - config
---

# TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE - Evidence namespace and project config/release split plan

## Goal

- Make evidence and project configuration navigable at current repository scale without rewriting immutable historical records.

## Scope

- Propose `reviews/` namespace or generated index migration rules that preserve old links.
- Split `agents/project/` into active config, policy, release evidence, and generated state categories.
- Coordinate with `TASK-AR-319` so evidence indexing and stale-doc checks share one source model.

## Acceptance Criteria

- The plan lists migration-safe paths and backlink preservation rules.
- `TASK-AR-319` remains the automation owner for generated evidence index work.
- No historical review/TASK closeout file is rewritten as part of the plan.

## Evidence Targets

- `reviews/INDEX.md`
- `agents/project/`
- `TASK-AR-319`
