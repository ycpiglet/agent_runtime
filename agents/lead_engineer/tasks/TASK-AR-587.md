---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-587
display_id: TASK-AR-587
task_uid: eea05fb1-6532-4646-9d2a-6b3dd25543fd
work_id: TASK-AR-587
work_uid: eea05fb1-6532-4646-9d2a-6b3dd25543fd
kind: task
parent_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
registered_at: 2026-06-20T01:04:15+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T01:04:15+09:00
title: Agent avatar identity system (DiceBear CC0 + role accent)
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-587/UNIT-TASK-AR-587-001.md
reservation_id: RES-20260620-010415-e5a1738e-01
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Give every agent a deterministic visual identity: a seeded SVG avatar keyed to agent id, plus a deterministic per-role accent, self-hosted and version-pinned.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-587 - Agent avatar identity system (DiceBear CC0 + role accent)

## Goal

- Give every agent a deterministic visual identity: a seeded SVG avatar keyed to agent id, plus a deterministic per-role accent, self-hosted and version-pinned.

## Scope

- Add a pattern_component patternAgentAvatar in ui_design_assets.py (experimental tier). Use DiceBear in seeded mode with a CC0 style (Notionists preferred; Open Peeps/Pixel Art acceptable). Do NOT depend on the live api.dicebear.com at runtime: pre-generate or vendor the style and self-host SVGs; pin the DiceBear major version. Layer a deterministic role accent (ring/background) drawn in our own SVG mapped to existing role/status tokens; verify WCAG contrast in dark and light. Record the exact CC0 style + version in the module docstring.

## Acceptance Criteria

- patternAgentAvatar renders a stable SVG avatar for a given agent id (same id -> same avatar) using a CC0 DiceBear style, with no runtime call to api.dicebear.com.
- A deterministic per-role accent (ring/background) maps to role/status tokens and meets WCAG AA contrast in both dark and light themes.
- The chosen style, its CC0 license, and the pinned DiceBear version are recorded in the asset module; no raw color/size literals (design_system_gate --all-ui passes).
- Avatar appears in at least one console view (e.g. agent cards / live agent map) with desktop+mobile visual_verification.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
