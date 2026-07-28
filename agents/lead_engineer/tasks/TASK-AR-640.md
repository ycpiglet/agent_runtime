---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-640
display_id: TASK-AR-640
task_uid: cefa88c8-fabb-4a03-8ee5-bd4e46cab9de
work_id: TASK-AR-640
work_uid: cefa88c8-fabb-4a03-8ee5-bd4e46cab9de
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T19:48:21+09:00
started_at: 2026-07-28T19:48:21+09:00
title: Introduce profile and ownership-aware host configuration
status: in_progress
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-640/UNIT-TASK-AR-640-001.md
reservation_id: RES-20260728-163601-b8c2a87a-02
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-194821-task-ar-640-640001.json
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Represent shared capabilities and host ownership without requiring a project-specific fork of the runtime.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-640 - Introduce profile and ownership-aware host configuration

## Goal

- Represent shared capabilities and host ownership without requiring a project-specific fork of the runtime.

## Scope

- Add config schema v2 with composable profiles, capabilities, host context, role overlay, state adapters, risk paths, and file ownership modes while preserving v1 config compatibility.

## Acceptance Criteria

- Existing v1 agent_runtime.yml files still parse.
- Profiles can select core, web-content, security-service, and full-runtime capabilities.
- Files can be classified as managed, seed_once, host_owned, or generated.
- HOST-CONTEXT and host role/risk/state mappings are machine-consumed.

## Verification

- `python -m pytest tests/test_doctor.py tests/test_project_context_overlay.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py -q`
