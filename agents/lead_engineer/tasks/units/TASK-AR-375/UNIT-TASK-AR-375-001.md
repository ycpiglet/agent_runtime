---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-375-001
work_uid: a36a4830-a91b-442a-b713-a9a108926452
kind: unit
parent_id: TASK-AR-375
unit_id: UNIT-TASK-AR-375-001
task_id: TASK-AR-375
task_set_id: TASKSET-AR-AGENT-IDENTITY-CONTRACT
initiative_id: INIT-AR-AGENT-IDENTITY-OBSERVABILITY
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-12T14:50:00+09:00
updated_at: 2026-06-12T15:25:35+09:00
origin_type: owner_request
origin_ref: reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
created_by: codex
summary: Agent Instance Registry And Gate Foundation
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Owner/Claude intake requires class-like roles to be distinguished from live agent instances. Existing claim records have agent_instance_id/display_name/callsite_id, but there is no durable spawn record or focused attribution gate.
inputs:
  - reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
  - scripts/task_claim_dispatcher.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - scripts/rbac_write_gate.py
target_files:
  - scripts/agent_instance_registry.py
  - scripts/agent_identity_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/pane_event_log.py
  - scripts/owner_governance_gate.py
  - tests/test_agent_identity_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_rbac_write_gate.py
  - tests/test_backlog_board_tasksets.py
  - agents/project/AGENT-IDENTITY-CONTRACT.md
  - src/agent_runtime/templates/project/scripts/agent_instance_registry.py
  - src/agent_runtime/templates/project/scripts/agent_identity_gate.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/pane_event_log.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
scope: Add instance spawn record creation for task claims and a deterministic gate that validates claim-to-instance attribution; do not build analytics UI, stats pivots, or broad A2A attribution migration in this unit.
acceptance:
  - Creating a task claim writes agents/runtime/instances/<agent_instance_id>.json with schema agent-runtime-agent-instance/v1.
  - Claim-created pane events use agent_instance_id as actor and preserve actor_role/display_name/callsite_id.
  - The instance record includes role, team_id, agent_instance_id, display_name, callsite_id, pane_id, spawned_at, spawned_by, task_id, task_set_id, worktree_path, model_tier, and claim_refs.
  - Re-running registry creation for the same claim is idempotent and does not duplicate claim_refs.
  - agent_identity_gate.py --check passes for claims with matching instance records and fails with exact findings for missing or mismatched records.
  - Owner governance and the reusable project template invoke/include the agent identity gate.
  - The contract document states role-only attribution is invalid for runtime artifacts.
verification:
  - python -m py_compile scripts/agent_instance_registry.py scripts/agent_identity_gate.py scripts/task_claim_dispatcher.py scripts/pane_event_log.py
  - python -m py_compile src/agent_runtime/templates/project/scripts/agent_instance_registry.py src/agent_runtime/templates/project/scripts/agent_identity_gate.py src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py src/agent_runtime/templates/project/scripts/pane_event_log.py src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - pytest tests/test_agent_identity_gate.py tests/test_task_claim_dispatcher.py tests/test_rbac_write_gate.py tests/test_backlog_board_tasksets.py -q
  - python scripts/agent_identity_gate.py --check
  - python scripts/task_unit_readiness_gate.py --task-id TASK-AR-375 --unit-id UNIT-TASK-AR-375-001 --require-ready --check
handoff: Report the instance record path, gate command, test coverage, and remaining analytics/A2A attribution gaps.
stop_condition: Stop after claim-created instance records and the attribution gate are implemented, verified, and recorded.
verified_at: 2026-06-12T15:18:10+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612150512.json
  - reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612151810.json
resolution: done
completed_at: 2026-06-12T15:25:35+09:00
closed_by: codex
actual_hours: 1.1
actual_tokens: 0
---

# UNIT-TASK-AR-375-001 - Agent Instance Registry And Gate Foundation

## Context

Owner/Claude intake requires class-like roles to be distinguished from live agent instances. Existing claim records have agent_instance_id/display_name/callsite_id, but there is no durable spawn record or focused attribution gate.

## Inputs

- reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
- scripts/task_claim_dispatcher.py
- docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
- scripts/rbac_write_gate.py

## Target Files

- scripts/agent_instance_registry.py
- scripts/agent_identity_gate.py
- scripts/task_claim_dispatcher.py
- scripts/pane_event_log.py
- scripts/owner_governance_gate.py
- tests/test_agent_identity_gate.py
- tests/test_task_claim_dispatcher.py
- tests/test_rbac_write_gate.py
- tests/test_backlog_board_tasksets.py
- agents/project/AGENT-IDENTITY-CONTRACT.md
- src/agent_runtime/templates/project/scripts/agent_instance_registry.py
- src/agent_runtime/templates/project/scripts/agent_identity_gate.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/pane_event_log.py
- src/agent_runtime/templates/project/scripts/owner_governance_gate.py

## Scope

Add instance spawn record creation for task claims and a deterministic gate that validates claim-to-instance attribution; do not build analytics UI, stats pivots, or broad A2A attribution migration in this unit.

## Steps

1. Add an instance registry helper/CLI that records claim-derived instance JSON under agents/runtime/instances/.
2. Wire task_claim_dispatcher create to write the spawn record after claim creation.
3. Add an agent identity gate that validates claim records against instance records.
4. Document the Role/Instance/Callsign contract and append-only boundary.
5. Add focused tests for record creation, idempotency, and gate findings.

## Acceptance Criteria

- Creating a task claim writes agents/runtime/instances/<agent_instance_id>.json with schema agent-runtime-agent-instance/v1.
- Claim-created pane events use agent_instance_id as actor and preserve actor_role/display_name/callsite_id.
- The instance record includes role, team_id, agent_instance_id, display_name, callsite_id, pane_id, spawned_at, spawned_by, task_id, task_set_id, worktree_path, model_tier, and claim_refs.
- Re-running registry creation for the same claim is idempotent and does not duplicate claim_refs.
- agent_identity_gate.py --check passes for claims with matching instance records and fails with exact findings for missing or mismatched records.
- Owner governance and the reusable project template invoke/include the agent identity gate.
- The contract document states role-only attribution is invalid for runtime artifacts.

## Verification

- `python -m py_compile scripts/agent_instance_registry.py scripts/agent_identity_gate.py scripts/task_claim_dispatcher.py scripts/pane_event_log.py`
- `python -m py_compile src/agent_runtime/templates/project/scripts/agent_instance_registry.py src/agent_runtime/templates/project/scripts/agent_identity_gate.py src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py src/agent_runtime/templates/project/scripts/pane_event_log.py src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- `pytest tests/test_agent_identity_gate.py tests/test_task_claim_dispatcher.py tests/test_rbac_write_gate.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/agent_identity_gate.py --check`
- `python scripts/task_unit_readiness_gate.py --task-id TASK-AR-375 --unit-id UNIT-TASK-AR-375-001 --require-ready --check`

## Handoff

Report the instance record path, gate command, test coverage, and remaining analytics/A2A attribution gaps.

## Stop Boundary

Stop after claim-created instance records and the attribution gate are implemented, verified, and recorded.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T15:25:35+09:00`
- Resolution: `done`
- Actual hours: `1.1`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612150512.json`
  - `reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612151810.json`
<!-- work-close:end -->