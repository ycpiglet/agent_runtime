---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-658
display_id: TASK-AR-658
task_uid: 412c4322-0275-4cef-a585-78dae071ae4a
work_id: TASK-AR-658
work_uid: 412c4322-0275-4cef-a585-78dae071ae4a
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
title: Expose Runtime operability health in the read-only UI
status: planned
priority: P2
difficulty: L
est_hours: 12
est_tokens: 23000
owner: uiux
team: ui-ux
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-658/UNIT-TASK-AR-658-001.md
reservation_id: RES-20260730-112500-842c7890-07
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Give the Owner one truthful view of routing economics, Scribe debt, Compound coverage, claim expiry, hooks, and pilot identity.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
depends_on:
  - TASK-AR-652
  - TASK-AR-653
  - TASK-AR-654
  - TASK-AR-655
  - TASK-AR-656
acceptance:
  - runtime_health exposes routing intent versus observation, token/cost budget, Scribe debt and coverage, Compound coverage, claim expiry, hook health, and latest pilot identity.
  - No credential, raw prompt, provider secret, or absolute local path reaches served state.
  - The view is read-only and does not grant migration, provider, or release authority.
  - Empty and unavailable states are explicit rather than rendered as zero savings or healthy.
  - Accessibility and browser smoke cover the new view.
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py -q
---

# TASK-AR-658 - Expose Runtime operability health in the read-only UI

## Goal

- Give the Owner one truthful view of routing economics, Scribe debt, Compound coverage, claim expiry, hooks, and pilot identity.

## Scope

- Add a secret-free read-only runtime_health resource and console view after the underlying receipt and lifecycle schemas stabilize.

## Acceptance Criteria

- runtime_health exposes routing intent versus observation, token/cost budget, Scribe debt and coverage, Compound coverage, claim expiry, hook health, and latest pilot identity.
- No credential, raw prompt, provider secret, or absolute local path reaches served state.
- The view is read-only and does not grant migration, provider, or release authority.
- Empty and unavailable states are explicit rather than rendered as zero savings or healthy.
- Accessibility and browser smoke cover the new view.

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py -q`
