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
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T19:48:21+09:00
started_at: 2026-07-28T19:48:21+09:00
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
  - reviews/REVIEW-2026-07-28-task-ar-640-w0-t3-replan.md
  - reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md
  - autofolio agent_runtime.yml audit findings
target_files:
  - src/agent_runtime/config.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/cli.py
  - tests/test_config_v2.py
  - tests/test_doctor.py
  - tests/test_host_context_read_location.py
  - docs/configuration-v2.md
scope: Implement bounded v1/v2 parsing, typed normalization, validation, HOST-CONTEXT consumption, and deterministic doctor JSON reporting. Do not change sync/lock application, profile manifests, adapter execution, or host files in this unit.
acceptance:
  - v1 fixtures remain green.
  - v2 profile and capability composition is deterministic and unknown identifiers block.
  - Invalid or unsafe ownership overlap is a blocker while v1 unmanaged_paths remains compatible.
  - Optional host context is consumed from one canonical path and invalid present context blocks.
  - doctor --json exposes the normalized effective configuration without changing --check behavior.
verification:
  - python -m pytest tests/test_config_v2.py tests/test_doctor.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py tests/test_project_context_overlay.py -q
handoff: Document the v1-to-v2 compatibility table and effective config JSON.
stop_condition: Stop before mutating a real host or introducing product-specific paths into core defaults.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-194821-task-ar-640-640001.json
---

# UNIT-TASK-AR-640-001 - Add backward-compatible profile and ownership config schema

## Context

AgentRuntimeConfig currently exposes only project, upstream, sync mode, overwrite policy, and exact unmanaged paths. That cannot express the Autofolio three-layer model without permanent seams.

## Inputs

- src/agent_runtime/config.py
- docs/host-context-read-location.md
- reviews/REVIEW-2026-07-28-task-ar-640-w0-t3-replan.md
- reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md
- autofolio agent_runtime.yml audit findings

## Target Files

- src/agent_runtime/config.py
- src/agent_runtime/doctor.py
- src/agent_runtime/cli.py
- tests/test_config_v2.py
- tests/test_doctor.py
- tests/test_host_context_read_location.py
- docs/configuration-v2.md

## Scope

Implement bounded v1/v2 parsing, typed normalization, validation,
`HOST-CONTEXT` consumption, and deterministic doctor JSON reporting. Do not
change sync/lock application, profile manifests, adapter execution, or host
files in this unit.

## Steps

1. Define typed source/effective schema, profile, capability, ownership, and
   host-adapter fields from the W0 contract.
2. Parse v1, bounded v2, and optional `host-context/v1` deterministically
   without a new YAML dependency.
3. Validate incompatible or unknown profile/capability combinations and
   unsafe mixed ownership.
4. Expose effective configuration through `doctor --json`, including valid
   JSON for invalid configuration.

## Acceptance Criteria

- v1 fixtures remain green.
- v2 profile and capability composition is deterministic and unknown
  identifiers block.
- Invalid or unsafe ownership overlap is a blocker while v1
  `unmanaged_paths` remains compatible.
- Optional host context is consumed from one canonical path and invalid
  present context blocks.
- `doctor --json` exposes the normalized effective configuration without
  changing `--check` behavior.

## Verification

- `python -m pytest tests/test_config_v2.py tests/test_doctor.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py tests/test_project_context_overlay.py -q`

## Handoff

Document the v1-to-v2 compatibility table and effective config JSON.

## Stop Boundary

Stop before mutating a real host or introducing product-specific paths into core defaults.
