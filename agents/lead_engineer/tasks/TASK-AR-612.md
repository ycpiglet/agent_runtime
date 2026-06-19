---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-612
display_id: TASK-AR-612
task_uid: 65d7c6c6-69b0-4133-84f9-99d8997c84ef
work_id: TASK-AR-612
work_uid: 65d7c6c6-69b0-4133-84f9-99d8997c84ef
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
registered_at: 2026-06-19T18:35:00+09:00
created_at: 2026-06-19T18:35:00+09:00
updated_at: 2026-06-19T18:35:00+09:00
title: Implement Taskset Board attention workspace assets
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 13000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-612/UNIT-TASK-AR-612-001.md
reservation_id: RES-20260619-183500-c4338bba-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-interface-designer-task-ar-611
summary: Convert the Taskset Board from a whole-board-first scan into an attention workspace with explainable lanes, taskset switcher, and relation detail while preserving the full searchable board fallback.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-612 - Implement Taskset Board attention workspace assets

## Goal

- Convert the Taskset Board from a whole-board-first scan into an attention workspace with explainable lanes, taskset switcher, and relation detail while preserving the full searchable board fallback.

## Scope

- Source mutation is allowed only inside the declared UI state, UI asset, design asset, and focused test files. Do not change task/claim SSoT files, write APIs, dispatcher behavior, or unrelated console views.

## Acceptance Criteria

- The Taskset Board first viewport exposes attention lanes for active claims, guarded or interrupted work, stale or missing evidence, recently changed tasksets, and ready next-action candidates before the all-tasksets fallback.
- Lane membership is derived from named schema fields and each card shows a visible reason label; state is never color-only.
- A keyboard-first taskset switcher supports known-target retrieval by id, title, alias, task id, and owner, with empty state and selected state.
- A relation detail panel preserves the existing operator_attention_graph semantics: taskset state, claim path, evidence freshness, graph or child context, and command readiness.
- Repeated lane, switcher, relation detail, state chip, and evidence preview surfaces are implemented as design assets or explicitly classified as one_off_for_now in closeout evidence.
- The existing Taskset Board API remains read-only and page/server files stay focused on data wiring and composition.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`
