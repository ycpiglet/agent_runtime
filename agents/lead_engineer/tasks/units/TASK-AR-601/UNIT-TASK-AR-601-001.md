---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-601-001
work_uid: 727a3175-4ddb-42b3-a66e-3a9cb97f9ac5
kind: unit
parent_id: TASK-AR-601
unit_id: UNIT-TASK-AR-601-001
task_id: TASK-AR-601
task_set_id: TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
initiative_id: INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-19T11:03:47+09:00
updated_at: 2026-07-19T11:03:47+09:00
origin_type: runtime_discovery
origin_ref: TASK-AR-594 closeout overlay release failure
created_by: codex-root-planner
summary: Repair overlay lifecycle artifacts and recursion guard
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - cross_cutting
  - data_integrity
context: TASK-AR-594 release generated two overlay claims without handoff/log pointers, so the standard release command refused them; after manual pointers, release would have routed nested overlays unless role routing was temporarily disabled.
inputs:
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-594-independent-auditor-closeout.json
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-594-skeptic-closeout.json
  - scripts/role_routing.py
  - scripts/task_claim_dispatcher.py
target_files:
  - scripts/role_routing.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - tests/test_role_routing.py
  - tests/test_role_routing_wiring.py
  - tests/test_task_claim_dispatcher.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Create atomic handoff/log records together with each overlay claim and skip role-review routing when the released claim is itself an overlay.
acceptance:
  - Generated overlay lifecycle pointers resolve to files.
  - Overlay release succeeds with evidence and does not create nested overlays.
  - Focused routing and dispatcher suites pass.
verification:
  - python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Report the original failure, lifecycle artifact paths, recursion guard behavior, and focused test output.
stop_condition: Stop if overlay claims require a separate lifecycle schema or if suppressing recursive routing would skip ordinary worker closeout reviews.
---

# UNIT-TASK-AR-601-001 - Repair overlay lifecycle artifacts and recursion guard

## Context

TASK-AR-594 release generated two overlay claims without handoff/log pointers, so the standard release command refused them; after manual pointers, release would have routed nested overlays unless role routing was temporarily disabled.

## Inputs

- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-594-independent-auditor-closeout.json
- agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-594-skeptic-closeout.json
- scripts/role_routing.py
- scripts/task_claim_dispatcher.py

## Target Files

- scripts/role_routing.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- tests/test_role_routing.py
- tests/test_role_routing_wiring.py
- tests/test_task_claim_dispatcher.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Create atomic handoff/log records together with each overlay claim and skip role-review routing when the released claim is itself an overlay.

## Steps

1. Add deterministic overlay handoff/log paths and atomic initial records.
2. Guard release-time routing for overlay claims while preserving ordinary release behavior.
3. Add end-to-end regression tests and refresh the host lock.

## Acceptance Criteria

- Generated overlay lifecycle pointers resolve to files.
- Overlay release succeeds with evidence and does not create nested overlays.
- Focused routing and dispatcher suites pass.

## Verification

- `python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Report the original failure, lifecycle artifact paths, recursion guard behavior, and focused test output.

## Stop Boundary

Stop if overlay claims require a separate lifecycle schema or if suppressing recursive routing would skip ordinary worker closeout reviews.
