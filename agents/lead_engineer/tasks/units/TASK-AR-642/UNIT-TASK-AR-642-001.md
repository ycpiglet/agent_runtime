---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-642-001
work_uid: e1da24f8-f250-43ba-af58-76a841827a80
kind: unit
parent_id: TASK-AR-642
unit_id: UNIT-TASK-AR-642-001
task_id: TASK-AR-642
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
summary: Implement ownership manifest and sync reconcile
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Autofolio must list host state and overlays as unmanaged, and one conflict causes the current sync apply to perform zero updates. Exact unmanaged paths cannot scale across heterogeneous hosts.
inputs:
  - src/agent_runtime/sync.py
  - src/agent_runtime/lock.py
  - src/agent_runtime/config.py
  - autofolio/docs/AGENT_RUNTIME_INTEGRATION.md
target_files:
  - src/agent_runtime/sync.py
  - src/agent_runtime/lock.py
  - src/agent_runtime/cli.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_template_smoke.py
scope: Implement ownership-aware planning, reconcile output, and explicit safe-only application. Do not auto-merge host edits.
acceptance:
  - No host-owned or generated file enters an apply set.
  - Safe-only apply is opt-in and reports skipped conflicts.
  - No silent overwrite path is introduced.
  - Legacy unmanaged config still behaves compatibly.
verification:
  - python -m pytest tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
handoff: Provide manifest examples for core, web-content, security-service, and Autofolio upgrade.
stop_condition: Stop before implementing automatic three-way merges.
---

# UNIT-TASK-AR-642-001 - Implement ownership manifest and sync reconcile

## Context

Autofolio must list host state and overlays as unmanaged, and one conflict causes the current sync apply to perform zero updates. Exact unmanaged paths cannot scale across heterogeneous hosts.

## Inputs

- src/agent_runtime/sync.py
- src/agent_runtime/lock.py
- src/agent_runtime/config.py
- autofolio/docs/AGENT_RUNTIME_INTEGRATION.md

## Target Files

- src/agent_runtime/sync.py
- src/agent_runtime/lock.py
- src/agent_runtime/cli.py
- tests/test_inventory_sync_sanitize.py
- tests/test_template_smoke.py

## Scope

Implement ownership-aware planning, reconcile output, and explicit safe-only application. Do not auto-merge host edits.

## Steps

1. Build the effective manifest from profile and ownership config.
2. Separate managed updates, seeds, host-owned files, generated views, and conflicts.
3. Add reconcile JSON and an explicit safe-only apply mode.
4. Lock the installed ownership manifest and pinned ref.

## Acceptance Criteria

- No host-owned or generated file enters an apply set.
- Safe-only apply is opt-in and reports skipped conflicts.
- No silent overwrite path is introduced.
- Legacy unmanaged config still behaves compatibly.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q`

## Handoff

Provide manifest examples for core, web-content, security-service, and Autofolio upgrade.

## Stop Boundary

Stop before implementing automatic three-way merges.
