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
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T23:42:28+09:00
started_at: 2026-07-28T23:42:28+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add profile-aware asset dependency closure and clean-host lifecycle smoke
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: At main b41fec24, source-side focused tests pass while a synced clean host omits eight advertised work/session/release/report commands and its shipped runtime-asset gate has two dangling registry paths. The W0 T3 contract requires one profile manifest shared by sync, adoption, lock, dependency validation, and wheel smoke.
inputs:
  - src/agent_runtime/templates/project/skills
  - src/agent_runtime/templates/project/scripts
  - tests/test_template_smoke.py
  - reviews/REVIEW-2026-07-28-task-ar-643-w0-t3-replan.md
target_files:
  - scripts/runtime_asset_usage.py
  - scripts/verify_wheel_dotfiles.py
  - src/agent_runtime/template_profiles.py
  - src/agent_runtime/sync.py
  - src/agent_runtime/adoption.py
  - src/agent_runtime/lock.py
  - src/agent_runtime/templates/project/scripts
  - src/agent_runtime/templates/project/skills
  - src/agent_runtime/templates/project/agents/project/RUNTIME-PROFILE-MANIFEST.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/.codex/hooks.json
  - tests/test_runtime_asset_usage.py
  - tests/test_template_smoke.py
  - tests/test_wheel_dotfiles_packaging.py
  - tests/test_adoption.py
  - tests/test_inventory_sync_sanitize.py
scope: Add one fail-closed profile manifest consumed by every template selector, close selected skill/doc/hook dependency gaps, ship only generic work/session/report helpers, and run clean-host plus built-wheel lifecycle smoke. Do not copy Agent Runtime release-project assets into consumer core.
acceptance:
  - Core, core plus web-content, core plus security-service, and full-runtime path sets are deterministic and use the same selection in sync, adoption, lock, and closure checks.
  - Every selected SKILL, documentation command, hook command, and registry path has an existing dependency inside the same effective profile set.
  - work.py, session baseline, dirty intake, and save-report execute in a clean installed host while product-specific release helpers are removed from consumer-facing promises.
  - A clean host completes status, registration, verification, closeout, report indexing, and dependency-gate smoke.
  - Built-wheel inspection proves the manifest, dotfiles, skills, work helper, session helpers, and save-report helper are present.
verification:
  - python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py tests/test_adoption.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/verify_wheel_dotfiles.py --check
  - python -m pytest -q
handoff: Report selected-file and dependency counts per profile, the eight baseline gaps and their resolution, clean-host lifecycle results, wheel contents, and any intentionally deferred product-specific edges.
stop_condition: Stop if closure would require shipping a product-specific role or path in core.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-234228-task-ar-643-643001.json
---

# UNIT-TASK-AR-643-001 - Add profile-aware asset dependency closure and clean-host lifecycle smoke

## Context

At Agent Runtime `main` `b41fec24`, the source-side focused suite passes while
a synced clean host omits eight advertised work/session/release/report command
paths. The host-side runtime-asset gate also fails on two dangling development
registry paths. The W0 T3 contract is
`reviews/REVIEW-2026-07-28-task-ar-643-w0-t3-replan.md`.

## Inputs

- src/agent_runtime/templates/project/skills
- src/agent_runtime/templates/project/scripts
- tests/test_template_smoke.py
- reviews/REVIEW-2026-07-28-task-ar-643-w0-t3-replan.md

## Target Files

- scripts/runtime_asset_usage.py
- scripts/verify_wheel_dotfiles.py
- src/agent_runtime/template_profiles.py
- src/agent_runtime/sync.py
- src/agent_runtime/adoption.py
- src/agent_runtime/lock.py
- src/agent_runtime/templates/project/scripts
- src/agent_runtime/templates/project/skills
- src/agent_runtime/templates/project/agents/project/RUNTIME-PROFILE-MANIFEST.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- src/agent_runtime/templates/project/.codex/hooks.json
- tests/test_runtime_asset_usage.py
- tests/test_template_smoke.py
- tests/test_wheel_dotfiles_packaging.py
- tests/test_adoption.py
- tests/test_inventory_sync_sanitize.py

## Scope

Add one fail-closed profile manifest consumed by every template selector, close
selected skill/document/hook dependency gaps, ship only generic
work/session/report helpers, and run clean-host plus built-wheel lifecycle
smoke. Do not copy Agent Runtime release-project assets into consumer core.

## Steps

1. Resolve deterministic core, web-content, security-service, and full-runtime
   path sets from the packaged manifest.
2. Make sync, adoption, lock, and closure validation consume that same set.
3. Parse selected skill, documentation, hook, and registry dependencies and
   fail on missing or cross-profile edges.
4. Ship generic work/session/report helpers and rewire product-specific
   release guidance rather than copying development-only release assets.
5. Exercise status, registration, verification, closeout, reporting, and the
   dependency gate from a clean host and inspect the built wheel.

## Acceptance Criteria

- All four effective profile combinations select deterministic file sets, and
  sync, adoption, lock, and dependency validation agree on them.
- Every selected SKILL, documentation command, hook command, and registry path
  has an existing dependency inside the same effective profile set.
- `work.py`, session baseline, dirty intake, and save-report execute in a clean
  installed host; product-specific release helpers are not copied into core.
- A clean host completes status, registration, verification, closeout, report
  indexing, and dependency-gate smoke.
- Built-wheel inspection proves the manifest, dotfiles, skills, and required
  lifecycle helpers are present.

## Verification

- `python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py tests/test_adoption.py tests/test_inventory_sync_sanitize.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python -m pytest -q`

## Handoff

Report selected-file and dependency counts per profile, the eight baseline
gaps and their resolution, clean-host lifecycle results, built-wheel contents,
and intentionally deferred product-specific edges.

## Stop Boundary

Stop if closure would require shipping a product-specific role or path in core.
