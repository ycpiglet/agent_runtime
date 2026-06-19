---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-591-001
work_uid: fcd1c242-5b57-490c-ab20-4ae23bd9871a
kind: unit
parent_id: TASK-AR-591
unit_id: UNIT-TASK-AR-591-001
task_id: TASK-AR-591
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
summary: Audit + wire components into live views
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Components from AR-587..590 exist in ui_design_assets.py but may only be wired into one view each. Ensure broad, consistent usage across the relevant served renderers in ui_console_assets.py.
inputs:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
scope: Wiring/integration only; do not redesign components. Preserve behavior elsewhere.
acceptance:
  - Each new component/token is used in its primary live view; gate green.
verification:
  - python -m pytest tests/test_ui_console.py tests/test_ui_design_assets.py -q
handoff: Integration wired; unit 2 boot-verifies.
stop_condition: If wiring a component requires a behavioral redesign, leave it and note it rather than scope-creep.
---

# UNIT-TASK-AR-591-001 - Audit + wire components into live views

## Context

Components from AR-587..590 exist in ui_design_assets.py but may only be wired into one view each. Ensure broad, consistent usage across the relevant served renderers in ui_console_assets.py.

## Inputs

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py

## Scope

Wiring/integration only; do not redesign components. Preserve behavior elsewhere.

## Steps

1. Grep the served renderers for agent listings, graph views, icon entities, metric surfaces, chart colors, and empty/error/loading; wire in the matching new component/token where missing.
2. Keep escaping symmetric and tokens-only.
3. Run the UI test suite + gate.

## Acceptance Criteria

- Each new component/token is used in its primary live view; gate green.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_design_assets.py -q`

## Handoff

Integration wired; unit 2 boot-verifies.

## Stop Boundary

If wiring a component requires a behavioral redesign, leave it and note it rather than scope-creep.
