---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-605
display_id: TASK-AR-605
task_uid: c27b747a-ef7a-47c6-b577-b3f849dc6e23
work_id: TASK-AR-605
work_uid: c27b747a-ef7a-47c6-b577-b3f849dc6e23
kind: task
parent_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
registered_at: 2026-06-19T12:26:00+09:00
created_at: 2026-06-19T12:26:00+09:00
started_at: 2026-06-19T12:40:31+09:00
updated_at: 2026-06-19T13:15:22+09:00
title: Refactor claim-aware operator relation pattern adapter
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 9000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-605/UNIT-TASK-AR-605-001.md
reservation_id: RES-20260619-122600-bbf35777-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Refactor the Operator Attention Graph relation pattern adapter for BTC-OAG-BLOCKED-001 and BTC-OAG-INTERRUPT-001 by feeding claim records into claim path and command readiness state.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-19T13:14:45+09:00
verified_by: codex-interface-designer-ar-605
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-605-20260619131445.json
resolution: done
completed_at: 2026-06-19T13:15:22+09:00
closed_by: codex-interface-designer-ar-605
actual_hours: 2.2
actual_tokens: 15000
---

# TASK-AR-605 - Refactor claim-aware operator relation pattern adapter

## Goal

- Refactor the Operator Attention Graph relation pattern adapter for BTC-OAG-BLOCKED-001 and BTC-OAG-INTERRUPT-001 by feeding claim records into claim path and command readiness state.

## Scope

- Source mutation is limited to the UI asset adapters and focused UI tests. Do not redesign the whole console, change routing architecture, or broaden visual styling beyond state semantics required by the findings.

## Acceptance Criteria

- Operator Attention Graph relation summary consumes `task_claims` or an equivalent claim-state projection when available.
- Active/resumed TASK-AR-604-style claim context no longer renders as `CLAIM PATH ready to claim` or `COMMAND READINESS task.create ready`.
- `tasksetChildRelationState` or its replacement exposes distinct `claimed`, `guarded`, and `interrupted` semantics instead of collapsing interrupted states to `stale`.
- Claim readiness and command readiness remain visible text, not color-only state.
- Touched UI is classified as design_token, ui_component, pattern_component, or one_off_for_now in verification evidence.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T13:15:22+09:00`
- Resolution: `done`
- Actual hours: `2.2`
- Actual tokens: `15000`
- Closed by: `codex-interface-designer-ar-605`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-605-20260619131445.json`
<!-- work-close:end -->
