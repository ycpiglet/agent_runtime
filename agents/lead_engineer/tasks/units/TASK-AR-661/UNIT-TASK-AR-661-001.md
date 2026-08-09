---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-661-001
work_uid: f7e1bbbd-1297-45c3-80b3-57f73487739f
kind: unit
parent_id: TASK-AR-661
unit_id: UNIT-TASK-AR-661-001
task_id: TASK-AR-661
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:20:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Repair work identity authority and prevent first-parent ledger loss
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: Merge 2db74f8f kept first-parent TASK-AR-653/654 and ledger bytes while losing six non-conflicting rows and the V080 Scribe/Compound task records. Existing gates validate ledger-to-task only and do not enforce registry membership in owner governance.
inputs:
  - reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
  - reviews/REVIEW-2026-08-09-task-ar-661-existing-taskset-recovery-t3-replan.md
  - agents/project/work-items/TASK-ID-RESERVATIONS.json
  - agents/project/work-items/TASKSET-DEFINITIONS.json
  - scripts/task_identity.py
  - scripts/taskset_work_gate.py
target_files:
  - scripts/task_identity.py
  - src/agent_runtime/templates/project/scripts/task_identity.py
  - scripts/taskset_work_gate.py
  - src/agent_runtime/templates/project/scripts/taskset_work_gate.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/work.py
  - scripts/plan_assumption_gate.py
  - src/agent_runtime/templates/project/scripts/plan_assumption_gate.py
  - schemas/work-identity-recovery.schema.json
  - src/agent_runtime/templates/project/schemas/work-identity-recovery.schema.json
  - agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
  - tests/test_task_identity.py
  - tests/test_taskset_work_gate.py
  - tests/test_taskset_dispatcher.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_work_registration.py
  - tests/test_plan_assumption_gate.py
  - tests/test_backlog_board_tasksets.py
  - tests/test_owner_governance_chain_parity.py
  - tests/test_owner_governance_consumer_host.py
  - tests/test_template_mirror_gate.py
scope: Implement gates and immutable recovery mapping in the worker. Shared task, unit, reservation-ledger, registry, pointer, and generated-view reconciliation remains orchestrator-owned W5 work.
acceptance:
  - The pre-fix repository reproduces both wrong-membership and missing-reservation REDs.
  - No invalid JSON merge strategy or display-ID overwrite is used.
  - Historical claim files remain byte-identical.
  - Owner governance transitively blocks every new identity finding.
  - Template gates remain usable with an absent or empty recovery registry.
  - A receipt-first existing-taskset transaction atomically reclassifies staged Tasks 662/663 with exact UUID and reservation CAS.
  - Path-only plan anchors cannot conceal a task_uid or unit work_uid substitution.
verification:
  - PYTHONPATH=src python -m pytest tests/test_task_identity.py tests/test_taskset_work_gate.py tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_registration.py tests/test_plan_assumption_gate.py tests/test_owner_governance_chain_parity.py tests/test_owner_governance_consumer_host.py tests/test_template_mirror_gate.py -q
  - PYTHONPATH=src python scripts/task_identity.py check --check
  - PYTHONPATH=src python scripts/taskset_work_gate.py --check
  - PYTHONPATH=src python scripts/owner_governance_gate.py --check
handoff: Attach RED output, exact restored-row diff, collision map and claim digests, V080 membership before/after, Host Gates evidence binding, historical artifact byte check, W4a, and independent W4b.
stop_condition: Stop before rewriting old 653/654 task or claim artifacts, union-merging JSON, granting recovery mappings claim-release authority, external CI, push, tag, publish, or deploy.
depends_on:
  - TASK-AR-660
---

# UNIT-TASK-AR-661-001 - Repair work identity authority and prevent first-parent ledger loss

## Context

Merge 2db74f8f kept first-parent TASK-AR-653/654 and ledger bytes while losing six non-conflicting rows and the V080 Scribe/Compound task records. Existing gates validate ledger-to-task only and do not enforce registry membership in owner governance.

## Inputs

- reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
- reviews/REVIEW-2026-08-09-task-ar-661-existing-taskset-recovery-t3-replan.md
- agents/project/work-items/TASK-ID-RESERVATIONS.json
- agents/project/work-items/TASKSET-DEFINITIONS.json
- scripts/task_identity.py
- scripts/taskset_work_gate.py

## Target Files

- scripts/task_identity.py
- src/agent_runtime/templates/project/scripts/task_identity.py
- scripts/taskset_work_gate.py
- src/agent_runtime/templates/project/scripts/taskset_work_gate.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/work.py
- scripts/plan_assumption_gate.py
- src/agent_runtime/templates/project/scripts/plan_assumption_gate.py
- schemas/work-identity-recovery.schema.json
- src/agent_runtime/templates/project/schemas/work-identity-recovery.schema.json
- agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
- tests/test_task_identity.py
- tests/test_taskset_work_gate.py
- tests/test_taskset_dispatcher.py
- tests/test_task_claim_dispatcher.py
- tests/test_work_registration.py
- tests/test_plan_assumption_gate.py
- tests/test_backlog_board_tasksets.py
- tests/test_owner_governance_chain_parity.py
- tests/test_owner_governance_consumer_host.py
- tests/test_template_mirror_gate.py

## Scope

Implement gates and immutable recovery mapping in the worker. Shared task, unit, reservation-ledger, registry, pointer, and generated-view reconciliation remains orchestrator-owned W5 work.

## Steps

1. RED missing/dangling/mismatched task reservation, wrong V080 membership, omitted 659, claim display-ID reuse, and tampered collision map.
2. Add task-to-ledger inverse exact linkage and taskset registry bidirectional membership validation.
3. RED and implement a receipt-first existing-taskset recovery transaction with exact task/unit UUID, reservation, registry, initiative, and plan-anchor CAS.
4. Validate a bounded immutable work-identity recovery registry with old/new UUID, claim path/digest, evidence, and commit ancestry bindings.
5. Make claim create/adopt and later mutations consume exact canonical work identity and refuse unresolved collision history.
6. After W4b, use the transaction under orchestrator authority to move Tasks 662/663 into V080, restore exactly six reservation rows, correct both taskset memberships, and reconcile Host Gates metadata from non-colliding evidence.
7. Re-anchor semantic plan identity, refresh pointer/generated views, run owner governance, and obtain final recovery evidence.

## Acceptance Criteria

- The pre-fix repository reproduces both wrong-membership and missing-reservation REDs.
- No invalid JSON merge strategy or display-ID overwrite is used.
- Historical claim files remain byte-identical.
- Owner governance transitively blocks every new identity finding.
- Template gates remain usable with an absent or empty recovery registry.
- A receipt-first existing-taskset transaction atomically reclassifies staged Tasks 662/663 with exact UUID and reservation CAS.
- Path-only plan anchors cannot conceal a task_uid or unit work_uid substitution.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_task_identity.py tests/test_taskset_work_gate.py tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_registration.py tests/test_plan_assumption_gate.py tests/test_owner_governance_chain_parity.py tests/test_owner_governance_consumer_host.py tests/test_template_mirror_gate.py -q`
- `PYTHONPATH=src python scripts/task_identity.py check --check`
- `PYTHONPATH=src python scripts/taskset_work_gate.py --check`
- `PYTHONPATH=src python scripts/owner_governance_gate.py --check`

## Handoff

Attach RED output, exact restored-row diff, collision map and claim digests, V080 membership before/after, Host Gates evidence binding, historical artifact byte check, W4a, and independent W4b.

## Stop Boundary

Stop before rewriting old 653/654 task or claim artifacts, union-merging JSON, granting recovery mappings claim-release authority, external CI, push, tag, publish, or deploy.
