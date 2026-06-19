---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-588
display_id: TASK-AR-588
task_uid: 51fd1ba5-1d9a-4ca4-ae46-d65d533ea474
work_id: TASK-AR-588
work_uid: 51fd1ba5-1d9a-4ca4-ae46-d65d533ea474
kind: task
parent_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
registered_at: 2026-06-20T01:04:15+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T04:42:00+09:00
title: Dependency / state-machine / live-agent graph upgrade (Dagre + d3-force)
status: completed
verification_status: passed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 20000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-588/UNIT-TASK-AR-588-001.md
reservation_id: RES-20260620-010415-e5a1738e-02
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Replace the hand-rolled graph layout with proper layout engines: Dagre (MIT, layered/Sugiyama) for dependency/org/state-machine DAGs and d3-force (ISC) for the free-form live agent map, both vendored build-less and rendered as our own SVG with Datadog/GitHub-style encodings.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verified_at: 2026-06-20T04:42:00+09:00
verified_by: codex-interface-designer-task-ar-588-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-588-graph-layout.json
resolution: done
completed_at: 2026-06-20T04:42:00+09:00
closed_by: codex-interface-designer-task-ar-588-20260620
---

# TASK-AR-588 - Dependency / state-machine / live-agent graph upgrade (Dagre + d3-force)

## Goal

- Replace the hand-rolled graph layout with proper layout engines: Dagre (MIT, layered/Sugiyama) for dependency/org/state-machine DAGs and d3-force (ISC) for the free-form live agent map, both vendored build-less and rendered as our own SVG with Datadog/GitHub-style encodings.

## Scope

- Vendor Dagre and d3-force as build-less <script>/UMD assets served by ui_console_assets.py (no CDN at runtime; record licenses). Feed graph data to the layout engine, then render with the existing/extended SVG pattern helpers (patternSvgGraph / patternSvgLayeredRadialLayout). Encode edges Datadog-style (stroke-width = magnitude, stroke color = health token) and add GitHub-Actions-style per-node status icons. Land as experimental; keep token-driven (no raw literals). Do NOT adopt elkjs (EPL-2.0) or 3d-force-graph (WebGL).

## Acceptance Criteria

- Dagre (MIT) and d3-force (ISC) are vendored and served locally (no runtime CDN); each library's license is recorded.
- Dependency/state-machine views use a Dagre layered layout rendered as our SVG; the live agent map uses d3-force tick-rendered SVG.
- Edges encode magnitude (stroke-width) and health (stroke color token); each node shows a status icon; status is never color-only.
- design_system_gate --all-ui passes (token-driven, no raw literals); desktop+mobile visual_verification of at least the dependency graph and live map.

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`

## W4a Self Verification (2026-06-20T04:18:13+09:00)

- Evidence: `reviews/VERIFY-2026-06-20-task-ar-588-graph-layout.json`.
- Tests: `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_console_e2e.py -q` -> `187 passed`.
- Design gate: `python scripts/design_system_gate.py --check --all-ui` -> pass.
- Browser verification: desktop and mobile dependency/state-machine/live-map views loaded locally served Dagre/d3-force assets, rendered status icons, magnitude edges, health edges, and no horizontal overflow.
