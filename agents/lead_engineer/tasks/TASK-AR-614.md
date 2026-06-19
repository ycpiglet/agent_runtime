---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-614
display_id: TASK-AR-614
task_uid: 5945f908-67ee-43eb-93e7-86517aea7383
work_id: TASK-AR-614
work_uid: 5945f908-67ee-43eb-93e7-86517aea7383
kind: task
parent_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
registered_at: 2026-06-19T21:56:00+09:00
created_at: 2026-06-19T21:56:00+09:00
updated_at: 2026-06-19T21:56:00+09:00
title: Fix Taskset attention active-claim freshness and empty lane copy
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 9000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-TSAW-CLAIM-EMPTY-REFINEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-614/UNIT-TASK-AR-614-001.md
reservation_id: RES-20260619-215600-10797311-01
origin_type: beta_finding
origin_ref: reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md
created_by: codex-ux-evaluator-ar-613
summary: Fix BTC-TSAW-CLAIM-001 and BTC-TSAW-EMPTY-001 so active runtime claims appear in the active_claims lane and zero-count lanes communicate recovery without contradictory copy.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-614 - Fix Taskset attention active-claim freshness and empty lane copy

## Goal

- Fix BTC-TSAW-CLAIM-001 and BTC-TSAW-EMPTY-001 so active runtime claims appear in the active_claims lane and zero-count lanes communicate recovery without contradictory copy.

## Scope

- Source mutation is limited to Taskset Board state derivation, attention lane pattern assets, and focused tests. Do not change task claim persistence, dispatcher release semantics, write APIs, or unrelated console views.

## Acceptance Criteria

- When task_claims contains a claimed task for a taskset, `attention_workspace.lanes.active_claims` includes that taskset with a visible active-claim reason.
- The selected taskset fallback prefers an active-claim taskset when one exists; otherwise it may fall back to ready/guarded/stale candidates.
- Zero-count attention lanes render empty-state copy that says no matching tasksets exist while preserving the lane purpose separately.
- State meaning remains textual and non-color-only for active, guarded, stale, empty, and ready-next lanes.
- Focused tests cover active claim derivation, empty lane copy, switcher/selected state preservation, and mobile CSS anchors.

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`
