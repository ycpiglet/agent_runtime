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
started_at: 2026-06-20T09:49:46+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T10:11:00+09:00
title: Agent avatar identity system (DiceBear CC0 + role accent)
status: completed
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
verification_status: passed
verified_at: 2026-06-20T10:11:00+09:00
verified_by: codex-independent-verifier-task-ar-587-20260620
evidence_refs:
  - reviews/VERIFY-2026-06-20-task-ar-587-avatar-identity.json
  - reviews/W4B-2026-06-20-TASK-AR-587.md
  - reviews/evidence/TASK-AR-587/avatar-identity-desktop.png
  - reviews/evidence/TASK-AR-587/avatar-identity-mobile.png
resolution: done
completed_at: 2026-06-20T10:11:00+09:00
closed_by: codex-interface-designer-task-ar-587-20260620
actual_hours: 2
actual_tokens: 6500
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

## Assetization Classification

| Surface | Class | Asset |
| --- | --- | --- |
| Deterministic agent avatar SVG | `pattern_component` | `patternAgentAvatar` |
| DiceBear Identicon style/version/license boundary | `served_asset` vendor record | `src/agent_runtime/vendor/dicebear/identicon/9.4.2` |
| Role accent mapping | `design_token` consumer | `_AVATAR_ROLE_ACCENT_PY` / `_AVATAR_ROLE_ACCENT` |
| Agent list avatar placement | `pattern_component` consumer | `agentCardTemplate` in `ui_console_assets.py` |
| Avatar pattern operating contract | design-system documentation | `docs/design/agent-runtime/DESIGN-SYSTEM.md` |

## Result

- Clarified the asset module docstring so it matches the actual DiceBear
  Identicon 9.4.2 vendor boundary, CC0 design license, MIT package/code license,
  and offline build-less renderer.
- Added a design-system contract entry and regression coverage for
  `patternAgentAvatar` as a TASK-AR-587 promoted pattern.
- Verified deterministic generation, no runtime `api.dicebear.com` dependency,
  token-driven role accents, and desktop/mobile rendering in `#/agents/list`.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-20T10:11:00+09:00`
- Resolution: `done`
- Actual hours: `2`
- Actual tokens: `6500`
- Closed by: `codex-interface-designer-task-ar-587-20260620`
- Evidence:
  - `reviews/VERIFY-2026-06-20-task-ar-587-avatar-identity.json`
  - `reviews/W4B-2026-06-20-TASK-AR-587.md`
  - `reviews/evidence/TASK-AR-587/avatar-identity-desktop.png`
  - `reviews/evidence/TASK-AR-587/avatar-identity-mobile.png`
<!-- work-close:end -->
