---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-592-002
work_uid: fea95f73-49a8-4c79-a65f-9ba6a5e65685
kind: unit
parent_id: TASK-AR-592
unit_id: UNIT-TASK-AR-592-002
task_id: TASK-AR-592
task_set_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
initiative_id: INIT-AR-VISUAL-SYSTEM-INTEGRATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-20T05:18:36+09:00
updated_at: 2026-06-20T05:18:36+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-autonomous-loop
created_by: lead-engineer
summary: Responsive pass for the new visuals
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Dense console must remain usable at mobile widths with the new graph/avatars/charts.
inputs:
  - src/agent_runtime/ui_console_assets.py (CSS)
  - the new component CSS
target_files:
  - src/agent_runtime/ui_console_assets.py
scope: Responsive CSS (token-driven) for the new visuals at mobile breakpoints.
acceptance:
  - New visuals usable at mobile widths; gate green.
verification:
  - python scripts/design_system_gate.py --check --all-ui
handoff: Visual system integration + a11y + responsive complete.
stop_condition: Keep responsive changes token-driven; never inline raw breakpoint literals outside the token layer if a token exists.
---

# UNIT-TASK-AR-592-002 - Responsive pass for the new visuals

## Context

Dense console must remain usable at mobile widths with the new graph/avatars/charts.

## Inputs

- src/agent_runtime/ui_console_assets.py (CSS)
- the new component CSS

## Target Files

- src/agent_runtime/ui_console_assets.py

## Scope

Responsive CSS (token-driven) for the new visuals at mobile breakpoints.

## Steps

1. Add/adjust responsive rules so avatars/graph/sparklines/state art degrade gracefully on narrow widths.
2. Keep tokens-only, no raw literals.
3. Verify the gate stays green.

## Acceptance Criteria

- New visuals usable at mobile widths; gate green.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`

## Handoff

Visual system integration + a11y + responsive complete.

## Stop Boundary

Keep responsive changes token-driven; never inline raw breakpoint literals outside the token layer if a token exists.
