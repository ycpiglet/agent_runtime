---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-657-001
work_uid: 76d26a83-3d40-40b3-9c23-07420e251aaa
kind: unit
parent_id: TASK-AR-657
unit_id: UNIT-TASK-AR-657-001
task_id: TASK-AR-657
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Package the reusable consumer-adoption operating procedure
horizon: unit
model_tier: worker_standard
escalation_triggers:
depends_on:
  - TASK-AR-654
  - TASK-AR-656
context: The Runtime has adopt/sync/migration CLIs and exact contracts, but no shipped trigger skill joins them into the safe sequence used by Bean Wiki, Allimbot, and Autofolio. failure-to-regression is also root-only.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - docs/pilot-acceptance-contract.md
  - docs/pilot-isolation-contract.md
  - skills/failure-to-regression/SKILL.md
target_files:
  - skills/runtime-adoption/SKILL.md
  - src/agent_runtime/templates/project/skills/runtime-adoption/SKILL.md
  - src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
  - skills/independent-verification/SKILL.md
  - skills/release-conductor/SKILL.md
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - tests/test_runtime_asset_usage.py
  - tests/test_template_smoke.py
  - tests/test_release_conductor_skill.py
scope: Package and enforce the proven procedure; do not add another agent role or a project-specific branch.
acceptance:
  - Consumers discover the procedure from the shipped Runtime.
  - Every migration uses the same exact evidence sequence.
  - Host overlays remain the only customization point.
  - No new agent role duplicates Scribe or Independent Auditor.
verification:
  - python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_pilot_acceptance.py tests/test_release_conductor_skill.py -q
handoff: Attach fresh-host skill discovery, stop-boundary tests, asset registry evidence, release-skill changes, and independent W4b.
stop_condition: Stop before running a real host migration, changing product files, creating a release, or adding a redundant agent role.
---

# UNIT-TASK-AR-657-001 - Package the reusable consumer-adoption operating procedure

## Context

The Runtime has adopt/sync/migration CLIs and exact contracts, but no shipped trigger skill joins them into the safe sequence used by Bean Wiki, Allimbot, and Autofolio. failure-to-regression is also root-only.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- docs/pilot-acceptance-contract.md
- docs/pilot-isolation-contract.md
- skills/failure-to-regression/SKILL.md

## Target Files

- skills/runtime-adoption/SKILL.md
- src/agent_runtime/templates/project/skills/runtime-adoption/SKILL.md
- src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
- skills/independent-verification/SKILL.md
- skills/release-conductor/SKILL.md
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- tests/test_runtime_asset_usage.py
- tests/test_template_smoke.py
- tests/test_release_conductor_skill.py

## Scope

Package and enforce the proven procedure; do not add another agent role or a project-specific branch.

## Steps

1. Author the runtime-adoption trigger and stop boundaries.
2. Ship both skills through the core template and asset registry.
3. Update verification and release skills to consume exact artifacts.
4. Add fresh-host discovery and forbidden-action tests.

## Acceptance Criteria

- Consumers discover the procedure from the shipped Runtime.
- Every migration uses the same exact evidence sequence.
- Host overlays remain the only customization point.
- No new agent role duplicates Scribe or Independent Auditor.

## Verification

- `python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_pilot_acceptance.py tests/test_release_conductor_skill.py -q`

## Handoff

Attach fresh-host skill discovery, stop-boundary tests, asset registry evidence, release-skill changes, and independent W4b.

## Stop Boundary

Stop before running a real host migration, changing product files, creating a release, or adding a redundant agent role.
