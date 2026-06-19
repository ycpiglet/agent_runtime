---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-590
display_id: TASK-AR-590
task_uid: ac39be71-7ce9-4632-9559-fe7e55ce51bb
work_id: TASK-AR-590
work_uid: ac39be71-7ce9-4632-9559-fe7e55ce51bb
kind: task
parent_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
registered_at: 2026-06-20T01:04:15+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T01:04:15+09:00
title: State illustrations + data-viz palette + sparklines
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-590/UNIT-TASK-AR-590-001.md
reservation_id: RES-20260620-010415-e5a1738e-04
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Add recolorable empty/error/loading illustrations, accessible data-viz palette tokens, and inline sparklines for at-a-glance trends.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-590 - State illustrations + data-viz palette + sparklines

## Goal

- Add recolorable empty/error/loading illustrations, accessible data-viz palette tokens, and inline sparklines for at-a-glance trends.

## Scope

- Vendor recolorable unDraw illustrations (recolor to accent token) wired into EmptyState/ErrorState/Loading patterns. Add categorical+sequential data-viz palette tokens from Radix Colors (MIT) + IBM Carbon data-viz (Apache), with dark+light + WCAG, for graph/chart use. Vendor fnando/sparkline (MIT) as componentSparkline. All permissive, self-hosted, token-driven, experimental.

## Acceptance Criteria

- Empty/Error/Loading states use recolorable unDraw illustrations tinted to the accent token (license recorded).
- Categorical + sequential data-viz palette tokens (Radix/Carbon) exist for both themes with WCAG-adequate contrast, consumed by the graph/charts.
- componentSparkline (fnando/sparkline, MIT) renders inline SVG trends; license recorded.
- design_system_gate --all-ui passes; desktop+mobile visual_verification of a state screen + a sparkline.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
