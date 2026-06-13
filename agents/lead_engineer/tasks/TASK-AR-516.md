---
id: TASK-AR-516
display_id: TASK-AR-516
task_uid: 0d48b9fe-4c6f-4ece-b298-3d3d8b738bb1
registered_at: 2026-06-12T23:32:00+09:00
created_at: 2026-06-12T23:32:00+09:00
updated_at: 2026-06-13T09:10:00+09:00
started_at: 2026-06-13T02:58:37+09:00
completed_at: 2026-06-13T09:10:00+09:00
title: Work Explorer tree roll-up and facet filters
status: completed
priority: P1
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - ui_surface
  - data_contract
tags:
  - work-explorer
  - ui
  - rollup
  - filters
---

# Work Explorer tree roll-up and facet filters

## Goal
- Make initiative/taskset/task/unit progress and metadata visible through one Work Explorer tree with computed roll-ups and facet filters.

## Context

- Owner does not want four disconnected tabs for initiative/taskset/task/unit.
- Current `BACKLOG-BOARD.md` is useful but still mostly a table; it hides
  completed archived context and does not expose roll-up/facet interaction.

## Scope

- Generalize the existing taskset/backlog view into a Work Explorer tree:
  Initiative -> Taskset -> Task -> Unit.
- Add level filters and facet filters for status, team, owner, model tier,
  risk, origin, component, and verification state.
- Compute roll-up progress from children only; do not store manual
  `progress_pct` as canonical data.
- Show archived completed A2A/taskset evidence when it is relevant to the
  selected node.

## Out Of Scope

- Arbitrary drag/drop editing of work hierarchy.
- Replacing `BACKLOG-BOARD.md` as the generated Owner summary.

## Acceptance Criteria

- Work Explorer shows `TASKSET-AR-WORK-METADATA-ANALYTICS` and its child tasks.
- Completed A2A tasks are discoverable from archived evidence, not invisible.
- Roll-up values change only from child state changes.

## Evidence Targets

- UI/API state changes + tests.
- Browser or console verification.
- Owner review with before/after screenshots or output excerpts.

## Completion Evidence

- PR #63 (ef0d29e): ui_state work_explorer resource (computed-only roll-ups, facets, evidence refs) + Work Explorer console tab (tree, depth/facet filters, archived evidence panel) + dual API routes; 1099 lines, 18 new tests.

## Verification Results

- pytest tests/test_ui_state.py tests/test_ui_console.py -q -> 45 passed
- pytest tests -q -> 582 passed (+1 pre-existing)
- real-repo demo: /api/work_explorer 200, metadata taskset rollup pct=17
- W4b inst-w4b-ar516-verifier -> APPROVE
