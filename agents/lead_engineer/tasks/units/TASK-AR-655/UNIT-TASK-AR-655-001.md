---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-655-001
work_uid: 250178c6-8aed-4bc0-855b-ab140bf44268
kind: unit
parent_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_id: TASK-AR-655
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-03T01:04:35+09:00
started_at: 2026-08-03T00:26:51+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Unify task-claim renewal and expiry consumers
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - repeated_failure
  - data_integrity
defect_signatures:
  - defect:negative-lease-or-grace-kills-live-claim:315a2daf2bae5424
  - defect:claim-reaper-deadline-overflow-partially-mutates:5d3658dc71ab217a
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-010343-bind-duration-domains-before-claim-authority-mut-c55c1cd29556.json
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260803-002651-task-ar-655-5f27.json
context: TASK-AR-650 continued well beyond its 30-minute lease, but the task claim dispatcher has only create, projection, and release commands. The separate low-level claim lease heartbeat is not connected to task claim JSON.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
  - reviews/REVIEW-2026-08-03-taskset-ar-v080-post-ar654-plan-revalidation.md
  - reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
  - reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/claim_lease.py
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
target_files:
  - src/agent_runtime/claim_store.py
  - scripts/agent_runtime/claim_store.py
  - src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/agent_orchestrator.py
  - scripts/claim_lease.py
  - src/agent_runtime/templates/project/scripts/claim_lease.py
  - scripts/claim_reaper.py
  - src/agent_runtime/templates/project/scripts/claim_reaper.py
  - scripts/deadlock_watchdog.py
  - src/agent_runtime/templates/project/scripts/deadlock_watchdog.py
  - scripts/state_sync_gate.py
  - src/agent_runtime/templates/project/scripts/state_sync_gate.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - scripts/worktree_lifecycle_gate.py
  - src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
  - src/agent_runtime/ui_state.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_claim_store.py
  - tests/test_claim_lease.py
  - tests/test_claim_reaper.py
  - tests/test_deadlock_watchdog.py
  - tests/test_claim_reaper_concurrency.py
  - tests/test_claim_reaper_hook.py
  - tests/test_state_sync_gate.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_worktree_lifecycle_gate.py
  - tests/test_ui_state.py
  - tests/test_template_mirror_gate.py
  - tests/test_regen_host_lock_if_needed.py
  - tests/test_lock_merge_driver.py
  - tests/fixtures/host/agent_runtime.lock.json
  - reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
  - reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
scope: Unify local lifecycle timestamps without creating a remote lease service.
acceptance:
  - Long tasks can remain legitimately active.
  - Stale workers cannot revive another owner's claim.
  - Replan renewal records old and new task, unit, target-file, and stop-boundary digests and cannot silently broaden scope.
  - Every surface agrees on active versus expired.
  - Renewal never commits or pushes host Git state.
  - Create lease is a plain integer of at least one minute and invalid or overflowing values leave no authority residue.
  - Low-level acquire and heartbeat TTL is a plain integer of at least one second and invalid or overflowing values leave no mutation.
  - Explicit reaper/watchdog grace is a plain integer of at least zero and is validated before either watchdog step.
  - Zero and equality boundaries, one-minute lease, environment normalization, and huge nonnegative grace remain safe and compatible.
  - Deadline overflow cannot split a sweep's durable mutations from its audit trail.
verification:
  - python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q
  - python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Attach the atomicity tests, owner mismatch, crash/restart, replan old/new scope digest proof, cross-consumer expiry matrix, and independent W4b.
stop_condition: Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.
verified_at: 2026-08-03T00:59:54+09:00
verified_by: le-20260803-001200-kst-ar655lease001
evidence_refs:
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803005954.json
---

# UNIT-TASK-AR-655-001 - Unify task-claim renewal and expiry consumers

## Context

TASK-AR-650 continued well beyond its 30-minute lease, but the task claim dispatcher has only create, projection, and release commands. The separate low-level claim lease heartbeat is not connected to task claim JSON.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
- reviews/REVIEW-2026-08-03-taskset-ar-v080-post-ar654-plan-revalidation.md
- reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
- reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
- reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/claim_lease.py
- src/agent_runtime/templates/project/scripts/state_sync_gate.py

## Target Files

- src/agent_runtime/claim_store.py
- scripts/agent_runtime/claim_store.py
- src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/agent_orchestrator.py
- scripts/claim_lease.py
- src/agent_runtime/templates/project/scripts/claim_lease.py
- scripts/claim_reaper.py
- src/agent_runtime/templates/project/scripts/claim_reaper.py
- scripts/deadlock_watchdog.py
- src/agent_runtime/templates/project/scripts/deadlock_watchdog.py
- scripts/state_sync_gate.py
- src/agent_runtime/templates/project/scripts/state_sync_gate.py
- scripts/parallel_worktree_gate.py
- src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
- scripts/worktree_lifecycle_gate.py
- src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
- src/agent_runtime/ui_state.py
- tests/test_task_claim_dispatcher.py
- tests/test_claim_store.py
- tests/test_claim_lease.py
- tests/test_claim_reaper.py
- tests/test_deadlock_watchdog.py
- tests/test_claim_reaper_concurrency.py
- tests/test_claim_reaper_hook.py
- tests/test_state_sync_gate.py
- tests/test_parallel_worktree_gate.py
- tests/test_worktree_lifecycle_gate.py
- tests/test_ui_state.py
- tests/test_template_mirror_gate.py
- tests/test_regen_host_lock_if_needed.py
- tests/test_lock_merge_driver.py
- tests/fixtures/host/agent_runtime.lock.json
- reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
- reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
- reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md

## Scope

Unify local lifecycle timestamps without creating a remote lease service.

## Steps

1. Add expiry and concurrent-renewal negative fixtures.
2. Add RED coverage for invalid create lease and explicit reaper/watchdog grace before changing implementation.
3. Add RED coverage for low-level acquire/heartbeat TTL and overflow-safe full-sweep auditing.
4. Implement fail-closed lease/grace value domains in root/template mirrors.
5. Implement atomic owner-checked heartbeat and renewal.
6. Wire orchestrator progress to the same mutation.
7. Adopt one expiry classifier in all read consumers.
8. Verify crash and restart behavior.

## Acceptance Criteria

- Long tasks can remain legitimately active.
- Stale workers cannot revive another owner's claim.
- Every surface agrees on active versus expired.
- Renewal never commits or pushes host Git state.
- Invalid or overflowing create lease leaves no claim authority or auxiliary residue.
- Invalid or overflowing low-level TTL leaves acquire and heartbeat state unchanged.
- Invalid explicit grace is rejected before either watchdog step or claim mutation.
- Zero/equality, one-minute, environment, and huge-grace compatibility is regression locked.
- Near-maximum deadlines cannot leave a partial sweep without its audit records.

## Verification

- `python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py -q`
- `python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py -q`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Attach the atomicity tests, owner mismatch, crash/restart, cross-consumer expiry matrix, and independent W4b.

## Stop Boundary

Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.
