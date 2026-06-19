---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-590-002
work_uid: 4100521f-7247-4641-bc64-104ef0da23a8
kind: unit
parent_id: TASK-AR-590
unit_id: UNIT-TASK-AR-590-002
task_id: TASK-AR-590
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T01:04:15+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Data-viz palette tokens + componentSparkline
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Graphs need accessible categorical/sequential palettes (Radix MIT / Carbon Apache) in both themes; sparklines give at-a-glance trends via fnando/sparkline (MIT).
inputs:
  - IBM Carbon data-viz palettes
  - Radix Colors
  - github.com/fnando/sparkline
  - the token layer
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
scope: Add data-viz palette tokens + vendor sparkline + componentSparkline helper.
acceptance:
  - Graph uses token palettes; componentSparkline renders inline; licenses recorded; gate green.
verification:
  - python -m pytest tests/test_design_system_gate.py -q
handoff: Visual-asset adoption complete.
stop_condition: Keep palettes token-driven; never inline raw hex outside the token layer.
---

# UNIT-TASK-AR-590-002 - Data-viz palette tokens + componentSparkline

## Context

Graphs need accessible categorical/sequential palettes (Radix MIT / Carbon Apache) in both themes; sparklines give at-a-glance trends via fnando/sparkline (MIT).

## Inputs

- IBM Carbon data-viz palettes
- Radix Colors
- github.com/fnando/sparkline
- the token layer

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py

## Scope

Add data-viz palette tokens + vendor sparkline + componentSparkline helper.

## Steps

1. Add categorical + sequential data-viz tokens (dark+light, WCAG) from Radix/Carbon; record licenses.
2. Point the graph node/edge colors at the categorical tokens.
3. Vendor fnando/sparkline (MIT); add componentSparkline(data) -> inline SVG.
4. Use a sparkline in a metric view (agent load / gate pass-rate).

## Acceptance Criteria

- Graph uses token palettes; componentSparkline renders inline; licenses recorded; gate green.

## Verification

- `python -m pytest tests/test_design_system_gate.py -q`

## Handoff

Visual-asset adoption complete.

## Stop Boundary

Keep palettes token-driven; never inline raw hex outside the token layer.
