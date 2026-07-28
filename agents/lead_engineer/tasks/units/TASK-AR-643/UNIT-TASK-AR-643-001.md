---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-643-001
work_uid: 00ab2d56-cd74-4e25-9e34-fef4b4730596
kind: unit
parent_id: TASK-AR-643
unit_id: UNIT-TASK-AR-643-001
task_id: TASK-AR-643
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add profile-aware asset dependency closure and clean-host lifecycle smoke
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The host template advertises independent-verification, work-analytics, release-conductor, and session-closeout skills while omitting several scripts they require.
inputs:
  - src/agent_runtime/templates/project/skills
  - src/agent_runtime/templates/project/scripts
  - tests/test_template_smoke.py
target_files:
  - scripts/runtime_asset_usage.py
  - src/agent_runtime/templates/project/scripts
  - src/agent_runtime/templates/project/skills
  - tests/test_runtime_asset_usage.py
  - tests/test_template_smoke.py
  - tests/test_wheel_dotfiles_packaging.py
scope: Close declared dependency gaps and run a clean-host lifecycle smoke. Do not copy unrelated root-only development assets into every profile.
acceptance:
  - The previously missing work, release, session, and save-report dependencies are resolved or removed from advertised profiles.
  - A clean host completes status, registration, verification, and closeout smoke.
  - Dotfiles and executable wrappers are present in the wheel.
verification:
  - python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py -q
handoff: Report dependency counts per profile and clean-host command results.
stop_condition: Stop if closure would require shipping a product-specific role or path in core.
---

# UNIT-TASK-AR-643-001 - Add profile-aware asset dependency closure and clean-host lifecycle smoke

## Context

The host template advertises independent-verification, work-analytics, release-conductor, and session-closeout skills while omitting several scripts they require.

## Inputs

- src/agent_runtime/templates/project/skills
- src/agent_runtime/templates/project/scripts
- tests/test_template_smoke.py

## Target Files

- scripts/runtime_asset_usage.py
- src/agent_runtime/templates/project/scripts
- src/agent_runtime/templates/project/skills
- tests/test_runtime_asset_usage.py
- tests/test_template_smoke.py
- tests/test_wheel_dotfiles_packaging.py

## Scope

Close declared dependency gaps and run a clean-host lifecycle smoke. Do not copy unrelated root-only development assets into every profile.

## Steps

1. Parse skill and hook dependencies from the selected manifest.
2. Fail on absent or cross-profile dangling dependencies.
3. Ship package entrypoints or thin wrappers for required lifecycle commands.
4. Exercise them from an installed wheel fixture.

## Acceptance Criteria

- The previously missing work, release, session, and save-report dependencies are resolved or removed from advertised profiles.
- A clean host completes status, registration, verification, and closeout smoke.
- Dotfiles and executable wrappers are present in the wheel.

## Verification

- `python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py -q`

## Handoff

Report dependency counts per profile and clean-host command results.

## Stop Boundary

Stop if closure would require shipping a product-specific role or path in core.
