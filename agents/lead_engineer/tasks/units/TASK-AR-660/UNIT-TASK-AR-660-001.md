---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-660-001
work_uid: 1807fd98-34ea-4bd6-b4eb-a29e4e35ada4
kind: unit
parent_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
task_id: TASK-AR-660
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:55:20+09:00
started_at: 2026-08-09T12:55:20+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Bind claim work identity and add receipt-first recovery WAL
horizon: unit
model_tier: worker_standard
escalation_triggers:
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260809-125520-task-ar-660-491d.json
last_actor_instance: le-20260809-130000-kst-ar660001
context: TASK-AR-659 records recovery digests only on stdout, activate-store can succeed after losing its only audit event, strict fsync outcomes are hidden, and claim files are bound only to reusable display IDs.
inputs:
  - reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
  - reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/claim_store.py
  - scripts/atomic_io.py
target_files:
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - scripts/role_routing.py
  - src/agent_runtime/templates/project/scripts/role_routing.py
  - src/agent_runtime/claim_store.py
  - scripts/agent_runtime/claim_store.py
  - src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py
  - scripts/atomic_io.py
  - src/agent_runtime/templates/project/scripts/atomic_io.py
  - new:scripts/recovery_receipt.py
  - new:src/agent_runtime/templates/project/scripts/recovery_receipt.py
  - new:schemas/recovery-receipt.schema.json
  - new:src/agent_runtime/templates/project/schemas/recovery-receipt.schema.json
  - scripts/pane_event_log.py
  - src/agent_runtime/templates/project/scripts/pane_event_log.py
  - scripts/runtime_asset_usage.py
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - new:tests/test_recovery_receipt.py
  - tests/test_atomic_io.py
  - tests/test_claim_store.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_role_routing.py
  - tests/test_template_mirror_gate.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Local filesystem claim authority only. Recovery receipts are machine authority; Markdown reviews remain explanation. Preserve the existing scope_binding wire format.
acceptance:
  - A display-ID collision or changed task/unit UUID blocks claim use.
  - Exact persisted receipt and predicted subject bytes reproduce their recorded hashes.
  - Receipt publication failure occurs before subject mutation.
  - A subject failure leaves only a prepared receipt and cannot be reported committed.
  - Already initialized activation creates no false recovery receipt or event.
verification:
  - PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_role_routing.py -q
  - PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
handoff: Attach RED commits, receipt state matrix, exact digest proof, crash/failure matrix, work-identity drift negatives, template parity, managed-lock proof, W4a, and independent W4b.
stop_condition: Stop before rotation, claim release/acceptance/completion, external CI, consumer mutation, credential access, push, tag, publish, or deploy.
---

# UNIT-TASK-AR-660-001 - Bind claim work identity and add receipt-first recovery WAL

## Context

TASK-AR-659 records recovery digests only on stdout, activate-store can succeed after losing its only audit event, strict fsync outcomes are hidden, and claim files are bound only to reusable display IDs.

## Inputs

- reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
- reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
- scripts/task_claim_dispatcher.py
- src/agent_runtime/claim_store.py
- scripts/atomic_io.py

## Target Files

- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- scripts/role_routing.py
- src/agent_runtime/templates/project/scripts/role_routing.py
- src/agent_runtime/claim_store.py
- scripts/agent_runtime/claim_store.py
- src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py
- scripts/atomic_io.py
- src/agent_runtime/templates/project/scripts/atomic_io.py
- new:scripts/recovery_receipt.py
- new:src/agent_runtime/templates/project/scripts/recovery_receipt.py
- new:schemas/recovery-receipt.schema.json
- new:src/agent_runtime/templates/project/schemas/recovery-receipt.schema.json
- scripts/pane_event_log.py
- src/agent_runtime/templates/project/scripts/pane_event_log.py
- scripts/runtime_asset_usage.py
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- new:tests/test_recovery_receipt.py
- tests/test_atomic_io.py
- tests/test_claim_store.py
- tests/test_task_claim_dispatcher.py
- tests/test_role_routing.py
- tests/test_template_mirror_gate.py
- tests/test_template_smoke.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Local filesystem claim authority only. Recovery receipts are machine authority; Markdown reviews remain explanation. Preserve the existing scope_binding wire format.

## Steps

1. RED identity-drift, missing/tampered receipt, receipt-sink, strict-fsync, activation crash-gap, pane-event-loss, and post-commit-indeterminate cases.
2. Resolve canonical task_uid and unit work_uid into a separate immutable work-identity binding and validate it on every claim mutation.
3. Add one canonical JSON encoder, strict receipt publication outcomes, schema, immutable receipt builder, validator, and check command.
4. Publish receipt-first for adopt, terminalize, and activate-store using a claim-store under-lock precommit transition callback.
5. Make pane events derived notifications and preserve receipt bindings through heartbeat and renew.
6. Mirror, inventory, regenerate the host lock, and prove no grandfather receipt is synthesized for the 2026-08-03 manual recovery.

## Acceptance Criteria

- A display-ID collision or changed task/unit UUID blocks claim use.
- Exact persisted receipt and predicted subject bytes reproduce their recorded hashes.
- Receipt publication failure occurs before subject mutation.
- A subject failure leaves only a prepared receipt and cannot be reported committed.
- Already initialized activation creates no false recovery receipt or event.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_role_routing.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q`

## Handoff

Attach RED commits, receipt state matrix, exact digest proof, crash/failure matrix, work-identity drift negatives, template parity, managed-lock proof, W4a, and independent W4b.

## Stop Boundary

Stop before rotation, claim release/acceptance/completion, external CI, consumer mutation, credential access, push, tag, publish, or deploy.
