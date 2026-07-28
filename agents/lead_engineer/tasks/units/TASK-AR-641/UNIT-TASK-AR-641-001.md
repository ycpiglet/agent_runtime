---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-641-001
work_uid: fbff3d52-fbaa-4ecf-8efd-78dd695aeea6
kind: unit
parent_id: TASK-AR-641
unit_id: UNIT-TASK-AR-641-001
task_id: TASK-AR-641
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
summary: Implement read-only brownfield adoption planner
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Current inventory produced thousands of review entries for Bean Wiki and Allimbot because generated trees were treated as source, while doctor reported installation absence as nineteen blockers instead of an adoption plan.
inputs:
  - src/agent_runtime/inventory.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/cli.py
  - Bean Wiki and Allimbot preflight counts
target_files:
  - src/agent_runtime/adoption.py
  - src/agent_runtime/inventory.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/cli.py
  - tests/test_adoption.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_doctor.py
scope: Produce a deterministic, read-only adoption plan and filter generated/ignored content. Do not apply changes in this unit.
acceptance:
  - Plan output is stable across repeated runs.
  - Generated dependency/build trees do not appear as host conflicts.
  - No file is written during adopt --plan.
  - Every proposed mutation names ownership and reason.
verification:
  - python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_doctor.py -q
handoff: Attach Bean Wiki and Allimbot before/after inventory counts and sample ownership plans.
stop_condition: Stop before adopt --apply or host file modification.
---

# UNIT-TASK-AR-641-001 - Implement read-only brownfield adoption planner

## Context

Current inventory produced thousands of review entries for Bean Wiki and Allimbot because generated trees were treated as source, while doctor reported installation absence as nineteen blockers instead of an adoption plan.

## Inputs

- src/agent_runtime/inventory.py
- src/agent_runtime/doctor.py
- src/agent_runtime/cli.py
- Bean Wiki and Allimbot preflight counts

## Target Files

- src/agent_runtime/adoption.py
- src/agent_runtime/inventory.py
- src/agent_runtime/doctor.py
- src/agent_runtime/cli.py
- tests/test_adoption.py
- tests/test_inventory_sync_sanitize.py
- tests/test_doctor.py

## Scope

Produce a deterministic, read-only adoption plan and filter generated/ignored content. Do not apply changes in this unit.

## Steps

1. Add generated and VCS-ignore aware inventory filtering.
2. Classify existing host harness assets.
3. Compute effective profile file set and ownership actions.
4. Expose text and JSON adopt plans plus pre-adoption doctor mode.

## Acceptance Criteria

- Plan output is stable across repeated runs.
- Generated dependency/build trees do not appear as host conflicts.
- No file is written during adopt --plan.
- Every proposed mutation names ownership and reason.

## Verification

- `python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py tests/test_doctor.py -q`

## Handoff

Attach Bean Wiki and Allimbot before/after inventory counts and sample ownership plans.

## Stop Boundary

Stop before adopt --apply or host file modification.
