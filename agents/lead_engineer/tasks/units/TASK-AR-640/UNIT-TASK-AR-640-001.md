---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-640-001
work_uid: d3b3746a-5a4f-47c2-bc2c-7733209c2c71
kind: unit
parent_id: TASK-AR-640
unit_id: UNIT-TASK-AR-640-001
task_id: TASK-AR-640
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
summary: Add backward-compatible profile and ownership config schema
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: AgentRuntimeConfig currently exposes only project, upstream, sync mode, overwrite policy, and exact unmanaged paths. That cannot express the Autofolio three-layer model without permanent seams.
inputs:
  - src/agent_runtime/config.py
  - docs/host-context-read-location.md
  - autofolio agent_runtime.yml audit findings
target_files:
  - src/agent_runtime/config.py
  - src/agent_runtime/doctor.py
  - tests/test_doctor.py
  - tests/test_host_context_read_location.py
  - docs/configuration-v2.md
scope: Implement parsing, validation, defaults, and doctor reporting for config v2. Do not implement sync application in this unit.
acceptance:
  - v1 fixtures remain green.
  - v2 profile composition is deterministic.
  - Invalid ownership overlap is a blocker.
  - Host context has one canonical path.
verification:
  - python -m pytest tests/test_doctor.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py -q
handoff: Document the v1-to-v2 compatibility table and effective config JSON.
stop_condition: Stop before mutating a real host or introducing product-specific paths into core defaults.
---

# UNIT-TASK-AR-640-001 - Add backward-compatible profile and ownership config schema

## Context

AgentRuntimeConfig currently exposes only project, upstream, sync mode, overwrite policy, and exact unmanaged paths. That cannot express the Autofolio three-layer model without permanent seams.

## Inputs

- src/agent_runtime/config.py
- docs/host-context-read-location.md
- autofolio agent_runtime.yml audit findings

## Target Files

- src/agent_runtime/config.py
- src/agent_runtime/doctor.py
- tests/test_doctor.py
- tests/test_host_context_read_location.py
- docs/configuration-v2.md

## Scope

Implement parsing, validation, defaults, and doctor reporting for config v2. Do not implement sync application in this unit.

## Steps

1. Define typed profile, capability, ownership, and host-adapter fields.
2. Parse v1 and v2 deterministically without a new YAML dependency.
3. Validate incompatible or unknown profile combinations.
4. Expose effective configuration through doctor JSON.

## Acceptance Criteria

- v1 fixtures remain green.
- v2 profile composition is deterministic.
- Invalid ownership overlap is a blocker.
- Host context has one canonical path.

## Verification

- `python -m pytest tests/test_doctor.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py -q`

## Handoff

Document the v1-to-v2 compatibility table and effective config JSON.

## Stop Boundary

Stop before mutating a real host or introducing product-specific paths into core defaults.
