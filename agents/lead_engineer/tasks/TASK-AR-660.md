---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-660
display_id: TASK-AR-660
task_uid: d74673e9-5820-495a-8f10-6fd1f2e96e8a
work_id: TASK-AR-660
work_uid: d74673e9-5820-495a-8f10-6fd1f2e96e8a
kind: task
parent_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
registered_at: 2026-08-09T12:00:00+09:00
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
title: Complete durable owner-bound claim recovery transactions
status: planned
priority: P1
difficulty: XL
est_hours: 24
est_tokens: 48000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-660/UNIT-TASK-AR-660-001.md
reservation_id: RES-20260809-120000-5c48af85-01
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Finish the missing TASK-AR-659 rotation path and make every recovery mutation independently auditable after stdout, pane events, or process state are gone.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - claim-recovery
  - data-integrity
  - repeated-failure
  - red-first
acceptance:
  - New and adopted claims bind the canonical task task_uid and unit work_uid; heartbeat, renew, release, and rotate reject identity drift.
  - Adopt, terminalize, activate-store, and rotate publish an immutable receipt before subject mutation and retain exact semantic and raw before/after digests plus Owner attribution.
  - Receipt failure leaves the subject byte-identical, post-write uncertainty is non-retry-safe, and pane-event loss cannot erase recovery authority.
  - Rotate changes one provably expired active claim in place, preserves task/unit/scope/branch authority, advances one revision, and never creates, deletes, completes, or releases a claim.
  - Old workers immediately lose mutation authority and current plus prior worker lineage is barred from independent release verification.
  - Old/new agent-instance truth, projections, handoff/log continuity, template parity, and host lock remain consistent.
verification:
  - PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_agent_instance_registry.py tests/test_agent_identity_gate.py tests/test_role_routing.py -q
  - PYTHONPATH=src python -m pytest tests/test_parallel_worktree_gate.py tests/test_rbac_write_gate.py tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
  - PYTHONPATH=src python scripts/recovery_receipt.py --check
  - PYTHONPATH=src python scripts/template_mirror_gate.py --check
  - PYTHONPATH=src python scripts/rbac_write_gate.py --check
---

# TASK-AR-660 - Complete durable owner-bound claim recovery transactions

## Goal

- Finish the missing TASK-AR-659 rotation path and make every recovery mutation independently auditable after stdout, pane events, or process state are gone.

## Scope

- Add canonical work-identity binding, immutable receipt-first recovery WAL semantics, strict durability outcomes, and in-place expired-claim owner rotation with worker lineage and verifier exclusion.

## Acceptance Criteria

- New and adopted claims bind the canonical task task_uid and unit work_uid; heartbeat, renew, release, and rotate reject identity drift.
- Adopt, terminalize, activate-store, and rotate publish an immutable receipt before subject mutation and retain exact semantic and raw before/after digests plus Owner attribution.
- Receipt failure leaves the subject byte-identical, post-write uncertainty is non-retry-safe, and pane-event loss cannot erase recovery authority.
- Rotate changes one provably expired active claim in place, preserves task/unit/scope/branch authority, advances one revision, and never creates, deletes, completes, or releases a claim.
- Old workers immediately lose mutation authority and current plus prior worker lineage is barred from independent release verification.
- Old/new agent-instance truth, projections, handoff/log continuity, template parity, and host lock remain consistent.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_agent_instance_registry.py tests/test_agent_identity_gate.py tests/test_role_routing.py -q`
- `PYTHONPATH=src python -m pytest tests/test_parallel_worktree_gate.py tests/test_rbac_write_gate.py tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q`
- `PYTHONPATH=src python scripts/recovery_receipt.py --check`
- `PYTHONPATH=src python scripts/template_mirror_gate.py --check`
- `PYTHONPATH=src python scripts/rbac_write_gate.py --check`
