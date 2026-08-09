---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-660-002
work_uid: 4a2c850e-5e2e-434c-8f41-2fa7c6c0a92d
kind: unit
parent_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-002
task_id: TASK-AR-660
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Implement owner-attributed in-place expired-claim rotation
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: TASK-AR-659 promised rotation but shipped only adopt, terminalize, and activate-store. Autofolio demonstrates the recovery need, but its manual rotation omitted prior-owner lineage, old-instance termination, and prior-worker verifier exclusion.
inputs:
  - reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
  - scripts/task_claim_dispatcher.py
  - scripts/agent_instance_registry.py
  - scripts/agent_identity_gate.py
  - reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md
target_files:
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - scripts/agent_instance_registry.py
  - src/agent_runtime/templates/project/scripts/agent_instance_registry.py
  - scripts/agent_identity_gate.py
  - src/agent_runtime/templates/project/scripts/agent_identity_gate.py
  - scripts/pane_event_log.py
  - src/agent_runtime/templates/project/scripts/pane_event_log.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - scripts/rbac_write_gate.py
  - src/agent_runtime/templates/project/scripts/rbac_write_gate.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - tests/test_task_claim_dispatcher.py
  - tests/test_agent_instance_registry.py
  - tests/test_agent_identity_gate.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_rbac_write_gate.py
  - tests/test_template_mirror_gate.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: In-place recovery of one adopted, provably expired active worker/orchestrator claim. Owner identity is durable attribution, not cryptographic authentication.
acceptance:
  - Exactly one concurrent beat/rotate or rotate/rotate mutation commits.
  - No successful rotation changes claim path or claim_id or creates/deletes a claim.
  - Legacy claims must be adopted before rotation and ambiguous canonical work identity always refuses.
  - Old instance termination and new instance spawn are durable and projections match the new revision.
  - Every prior worker is excluded from independent release verification.
verification:
  - PYTHONPATH=src python -m pytest tests/test_task_claim_dispatcher.py tests/test_claim_store.py tests/test_recovery_receipt.py tests/test_agent_instance_registry.py tests/test_agent_identity_gate.py tests/test_parallel_worktree_gate.py tests/test_rbac_write_gate.py -q
  - PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
handoff: Attach Autofolio-shaped regression, exact before/after receipt, race evidence, lineage/verifier negative, old/new instance evidence, no-new-claim proof, W4a, and independent W4b.
stop_condition: Stop before changing task/unit/scope/branch authority, accepting indeterminate liveness by default, release/accept/complete/delete, external CI, push, tag, publish, or deploy.
depends_on:
  - UNIT-TASK-AR-660-001
---

# UNIT-TASK-AR-660-002 - Implement owner-attributed in-place expired-claim rotation

## Context

TASK-AR-659 promised rotation but shipped only adopt, terminalize, and activate-store. Autofolio demonstrates the recovery need, but its manual rotation omitted prior-owner lineage, old-instance termination, and prior-worker verifier exclusion.

## Inputs

- reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
- scripts/task_claim_dispatcher.py
- scripts/agent_instance_registry.py
- scripts/agent_identity_gate.py
- reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md

## Target Files

- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- scripts/agent_instance_registry.py
- src/agent_runtime/templates/project/scripts/agent_instance_registry.py
- scripts/agent_identity_gate.py
- src/agent_runtime/templates/project/scripts/agent_identity_gate.py
- scripts/pane_event_log.py
- src/agent_runtime/templates/project/scripts/pane_event_log.py
- scripts/parallel_worktree_gate.py
- src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
- scripts/rbac_write_gate.py
- src/agent_runtime/templates/project/scripts/rbac_write_gate.py
- docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
- src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
- tests/test_task_claim_dispatcher.py
- tests/test_agent_instance_registry.py
- tests/test_agent_identity_gate.py
- tests/test_parallel_worktree_gate.py
- tests/test_rbac_write_gate.py
- tests/test_template_mirror_gate.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

In-place recovery of one adopted, provably expired active worker/orchestrator claim. Owner identity is durable attribution, not cryptographic authentication.

## Steps

1. RED expired success, legacy-adopt sequence, live/terminal/overlay/indeterminate refusals, every CAS dimension, task UID replacement, races, receipt failure, and history-cap behavior.
2. Require expected raw digest, revision, old agent/callsite, scope digest, work-identity digest, initialized store snapshot, Owner identity, and reason.
3. Atomically rotate identity and complete lease tuple while preserving task, unit, taskset, scope, branch, role, team, model, progress, and claimed_at.
4. Append bounded worker lineage, terminate the old instance, spawn the new instance, refresh projection/handoff/log, and emit a receipt-bound rotation notification.
5. Reject current or prior worker identities as the release verifier and prove old heartbeat fails while new heartbeat succeeds.
6. Mirror documentation and implementation, regenerate the host lock, then obtain independent W4b.

## Acceptance Criteria

- Exactly one concurrent beat/rotate or rotate/rotate mutation commits.
- No successful rotation changes claim path or claim_id or creates/deletes a claim.
- Legacy claims must be adopted before rotation and ambiguous canonical work identity always refuses.
- Old instance termination and new instance spawn are durable and projections match the new revision.
- Every prior worker is excluded from independent release verification.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_task_claim_dispatcher.py tests/test_claim_store.py tests/test_recovery_receipt.py tests/test_agent_instance_registry.py tests/test_agent_identity_gate.py tests/test_parallel_worktree_gate.py tests/test_rbac_write_gate.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q`

## Handoff

Attach Autofolio-shaped regression, exact before/after receipt, race evidence, lineage/verifier negative, old/new instance evidence, no-new-claim proof, W4a, and independent W4b.

## Stop Boundary

Stop before changing task/unit/scope/branch authority, accepting indeterminate liveness by default, release/accept/complete/delete, external CI, push, tag, publish, or deploy.
