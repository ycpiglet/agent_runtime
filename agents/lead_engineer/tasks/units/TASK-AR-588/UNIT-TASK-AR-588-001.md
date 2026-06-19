---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-588-001
work_uid: 6b76d6ed-bce8-44a2-831b-964ba11cbe99
kind: unit
parent_id: TASK-AR-588
unit_id: UNIT-TASK-AR-588-001
task_id: TASK-AR-588
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T04:42:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Vendor Dagre + layered DAG renderer for dependency/state-machine
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Dagre is layout-only (emits node {x,y} + edge point arrays) and ships an IIFE global via <script>. Render with our own SVG; avoid dagre-d3 (pulls in D3).
inputs:
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 1)
  - src/agent_runtime/ui_design_assets.py (patternSvgGraph)
  - src/agent_runtime/ui_console_assets.py
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_console.py
scope: Vendor dagre.min.js locally; add a layered-DAG render path feeding the existing SVG graph pattern; Datadog edge + GitHub status encodings.
acceptance:
  - Dependency/state-machine graph uses Dagre layout rendered as our token-driven SVG with status-bearing nodes/edges.
verification:
  - python -m pytest tests/test_ui_console.py -q
handoff: Structured graph done; unit 2 does the force map.
stop_condition: If Dagre cannot be vendored build-less, stop and flag (do not fall back to elkjs/EPL-2.0).
verified_at: 2026-06-20T04:42:00+09:00
verified_by: codex-interface-designer-task-ar-588-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-588-graph-layout.json
resolution: done
completed_at: 2026-06-20T04:42:00+09:00
closed_by: codex-interface-designer-task-ar-588-20260620
---

# UNIT-TASK-AR-588-001 - Vendor Dagre + layered DAG renderer for dependency/state-machine

## Context

Dagre is layout-only (emits node {x,y} + edge point arrays) and ships an IIFE global via <script>. Render with our own SVG; avoid dagre-d3 (pulls in D3).

## Inputs

- reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 1)
- src/agent_runtime/ui_design_assets.py (patternSvgGraph)
- src/agent_runtime/ui_console_assets.py

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_console.py

## Scope

Vendor dagre.min.js locally; add a layered-DAG render path feeding the existing SVG graph pattern; Datadog edge + GitHub status encodings.

## Steps

1. Vendor dagre.min.js (MIT) into served assets; record license.
2. Compute a top-down/L-R layered layout; map coordinates onto our SVG nodes/edges.
3. Encode edge stroke-width=magnitude, stroke color=health token; add per-node status icon (from the icon set).
4. Apply to the dependency graph and state-machine views.

## Acceptance Criteria

- Dependency/state-machine graph uses Dagre layout rendered as our token-driven SVG with status-bearing nodes/edges.

## Verification

- `python -m pytest tests/test_ui_console.py -q`

## W4a Result

- Evidence: `reviews/VERIFY-2026-06-20-task-ar-588-graph-layout.json`.
- Dependency and state-machine SVG views serve local `@dagrejs/dagre` and use `patternSvgLayeredDagreLayout` to prefer the vendored Dagre runtime, with status badges/icons, magnitude edges, and health token classes.

## Handoff

Structured graph done; unit 2 does the force map.

## Stop Boundary

If Dagre cannot be vendored build-less, stop and flag (do not fall back to elkjs/EPL-2.0).
