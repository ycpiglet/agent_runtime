---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-607
display_id: TASK-AR-607
task_uid: 3a55de67-6cf7-4690-9c0d-e32ae27dafa0
work_id: TASK-AR-607
work_uid: 3a55de67-6cf7-4690-9c0d-e32ae27dafa0
kind: task
parent_id: TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
registered_at: 2026-06-19T14:04:00+09:00
created_at: 2026-06-19T14:04:00+09:00
updated_at: 2026-06-19T14:04:00+09:00
title: Fix Taskset Board mobile overflow
status: planned
priority: P1
difficulty: M
est_hours: 3
est_tokens: 8000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-607/UNIT-TASK-AR-607-001.md
reservation_id: RES-20260619-140400-41cd76a8-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Fix BTC-OAG-CLAIM-MOBILE-001 by constraining Taskset Board, relation-panel, toolbar, and child-row layout so the board fits a 390px mobile viewport without losing claim-aware labels.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-607 - Fix Taskset Board mobile overflow

## Goal

- Fix BTC-OAG-CLAIM-MOBILE-001 by constraining Taskset Board, relation-panel, toolbar, and child-row layout so the board fits a 390px mobile viewport without losing claim-aware labels.

## Scope

- Source mutation is limited to responsive CSS/layout helpers and focused tests. Do not change claim semantics, command-routing behavior, navigation IA, or introduce a new visual direction.

## Acceptance Criteria

- Taskset Board fits a 390px viewport after opening `More -> Taskset Board`; no document-level horizontal overflow remains.
- Relation panel preserves explicit `claimed`, `guarded`, `interrupted`, and no-claim labels from TASK-AR-605/TASK-AR-606.
- Responsive constraints use existing design tokens and pattern/component classes, not page-local hardcoded styling.
- Toolbar, add-task row, relation chips, evidence/context body, child rows, and swimlanes wrap or stack predictably on mobile.
- Focused tests cover the CSS/mobile contract and the claim-aware state contract.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
