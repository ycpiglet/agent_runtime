---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-588-002
work_uid: 0bc61782-974d-4c67-a88c-a70f00e0f372
kind: unit
parent_id: TASK-AR-588
unit_id: UNIT-TASK-AR-588-002
task_id: TASK-AR-588
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T11:49:51+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Vendor d3-force + live agent map renderer
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: d3-force is a velocity-Verlet layout that mutates node.x/.y and fires tick; we render SVG per tick. Confirm ISC license + a standalone UMD artifact.
inputs:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - the live agent map view
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
scope: Vendor d3-force build-less; tick-render the live agent map as our SVG with agent avatars as nodes.
acceptance:
  - Live agent map renders via d3-force as token-driven SVG with avatar nodes; license recorded.
verification:
  - python scripts/design_system_gate.py --check --all-ui
handoff: Graph upgrade complete.
stop_condition: If a build-less ISC d3-force artifact cannot be confirmed, flag before vendoring.
verified_at: 2026-06-20T11:44:21+09:00
verified_by: codex-interface-designer-task-ar-588-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-unit-task-ar-588-002-20260620114421.json
resolution: done
completed_at: 2026-06-20T11:49:51+09:00
closed_by: codex-interface-designer-task-ar-588-20260620
actual_hours: 3.0
actual_tokens: 9000
---

# UNIT-TASK-AR-588-002 - Vendor d3-force + live agent map renderer

## Context

d3-force is a velocity-Verlet layout that mutates node.x/.y and fires tick; we render SVG per tick. Confirm ISC license + a standalone UMD artifact.

## Inputs

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- the live agent map view

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py

## Scope

Vendor d3-force build-less; tick-render the live agent map as our SVG with agent avatars as nodes.

## Steps

1. Confirm d3-force ISC license + vendor a standalone UMD build (no CDN).
2. Wire tick-driven SVG rendering of the live agent map.
3. Use patternAgentAvatar nodes + health-encoded edges.
4. Verify interactivity (drag/zoom optional) and dark/light.

## Acceptance Criteria

- Live agent map renders via d3-force as token-driven SVG with avatar nodes; license recorded.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`

## Handoff

Graph upgrade complete.

## Stop Boundary

If a build-less ISC d3-force artifact cannot be confirmed, flag before vendoring.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T11:49:51+09:00`
- Resolution: `done`
- Actual hours: `3.0`
- Actual tokens: `9000`
- Closed by: `codex-interface-designer-task-ar-588-20260620`
- Evidence:
  - `reviews/VERIFY-2026-06-20-unit-task-ar-588-002-20260620114421.json`
<!-- work-close:end -->
