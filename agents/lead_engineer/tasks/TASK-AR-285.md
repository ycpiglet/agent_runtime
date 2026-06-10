---
id: TASK-AR-285
display_id: TASK-AR-285
task_uid: 49555bdd-520d-4041-9ecb-554f32aa0aa1
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: ""
updated_at: 2026-06-11T01:45:00+09:00
completed_at: ""
title: Build live multi-pane census
status: planned
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - claims
  - worktree
  - census
---

# TASK-AR-285 - Build live multi-pane census

## Goal

- Count and classify live pane, claim, task-set, worktree, and event evidence in one repeatable command.

## Scope

- Add a census script that reads task claims, pane events, worktree references, active task sets, and handoff logs.
- Report active, released, completed, stale, missing-worktree, missing-event, and missing-handoff counts.
- Separate current runtime state from historical completed task sets.
- Produce machine-readable JSON and Owner-readable summary output.

## Acceptance Criteria

- Census output identifies whether 5+ panes are actually active or only historical.
- Every active claim is mapped to task id, task set id, agent role, worktree path, branch, phase, and heartbeat.
- Missing runtime folders are reported as data gaps, not as proof that no collaboration happened.
- Output can be consumed by UI state and governance gates.

## Evidence Targets

- `scripts/multipane_census.py`
- `tests/test_multipane_census.py`
- `reviews/REVIEW-2026-06-10-agent-runtime-parallel-collaboration-audit.md`

