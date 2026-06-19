---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-587-001
work_uid: 4b6e4fc4-9bdd-4665-a791-5a6d3599983f
kind: unit
parent_id: TASK-AR-587
unit_id: UNIT-TASK-AR-587-001
task_id: TASK-AR-587
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
summary: Vendor + self-host a CC0 DiceBear style and add patternAgentAvatar
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: DiceBear is MIT but per-style licensed; Notionists/Open Peeps/Pixel Art are CC0. Determinism + license hold only within a major version, and the free API is rate-limited/non-commercial, so self-host.
inputs:
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 2)
  - src/agent_runtime/ui_design_assets.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md (assetization + maturity tiers)
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_design_assets.py
scope: Vendor/pre-generate a single CC0 style; add a seeded patternAgentAvatar helper returning SVG; no runtime CDN dependency.
acceptance:
  - Same agent id yields identical avatar SVG; no api.dicebear.com call at runtime.
verification:
  - python -m pytest tests/test_ui_design_assets.py -q
handoff: Avatar helper ready; unit 2 adds role accent + console placement.
stop_condition: If a CC0 style cannot be vendored offline cleanly, stop and flag rather than depending on the live API.
---

# UNIT-TASK-AR-587-001 - Vendor + self-host a CC0 DiceBear style and add patternAgentAvatar

## Context

DiceBear is MIT but per-style licensed; Notionists/Open Peeps/Pixel Art are CC0. Determinism + license hold only within a major version, and the free API is rate-limited/non-commercial, so self-host.

## Inputs

- reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (Strand 2)
- src/agent_runtime/ui_design_assets.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md (assetization + maturity tiers)

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_design_assets.py

## Scope

Vendor/pre-generate a single CC0 style; add a seeded patternAgentAvatar helper returning SVG; no runtime CDN dependency.

## Steps

1. Pick a CC0 style (Notionists) and pin the DiceBear major version.
2. Pre-generate or vendor the style so avatars resolve offline.
3. Add patternAgentAvatar(seed) -> SVG string in ui_design_assets.py, classified experimental.
4. Record style+license+version in the module docstring.
5. Add a determinism test (same seed -> identical SVG).

## Acceptance Criteria

- Same agent id yields identical avatar SVG; no api.dicebear.com call at runtime.

## Verification

- `python -m pytest tests/test_ui_design_assets.py -q`

## Handoff

Avatar helper ready; unit 2 adds role accent + console placement.

## Stop Boundary

If a CC0 style cannot be vendored offline cleanly, stop and flag rather than depending on the live API.
