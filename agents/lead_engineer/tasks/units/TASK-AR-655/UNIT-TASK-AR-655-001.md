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
w4b_acceptance: true
w4b_ref: reviews/W4B-2026-08-04-unit-task-ar-655-001-lease-truthfulness-final.md
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-03T08:21:50+09:00
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
  - defect:task-claim-progress-outlives-unrenewed-lease:9dae21269ca06d88
  - defect:expired-task-claim-appears-live-across-runtime-c:39f0d2087c60993c
  - defect:concurrent-task-claim-renewal-overwrites-newer-o:c22a19adb1ea01e9
  - defect:task-claim-renewal-silently-broadens-scope-witho:972c3033ed564ed9
  - defect:agent-orchestrator-claim-progress-acknowledges-s:865827031e86d0ca
  - defect:agent-instance-registry-concurrent-publish-rolls:609cd581edd3cea9
  - defect:claim-projection-without-explicit-now-skips-live:f96238afdd1aa3f9
  - defect:role-routing-overlay-claim-omits-lease-deadline:01470e887b26aa2b
  - defect:agent-instance-registry-mixes-revision-timestamp:1997c0b1b3471da3
  - defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe
  - defect:ui-console-cockpit-render-dereferences-runtime-s:cfd7f51f9ac8179b
  - defect:ui-console-pre-load-summary-fabricates-healthy-z:e18e21bcf63e1ade
compound_refs:
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-010343-bind-duration-domains-before-claim-authority-mut-c55c1cd29556.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-041700-bind-claim-progress-to-one-lease-revision-transa-77631cec1af6.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-050159-bind-claim-progress-projection-to-committed-clai-2398011ac247.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-055857-bind-current-agent-projection-to-canonical-claim-dec8884408f5.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-055906-keep-cockpit-rendering-null-safe-before-runtime-6bf65a1deb05.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-070945-bind-the-complete-pointer-agent-to-canonical-cla-9232deaaf17d.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-070957-keep-pre-load-cockpit-summaries-neutral-d2921d2f4e9d.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260803-080831-require-type-strict-complete-pointer-authority-200381d73cd9.json
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260804-121045-task-ar-655-0427.json
context: TASK-AR-650 continued well beyond its 30-minute lease, but the task claim dispatcher has only create, projection, and release commands. The separate low-level claim lease heartbeat is not connected to task claim JSON.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/AUDIT-2026-08-02-task-ar-654-combined-green-precommit.md
  - reviews/REVIEW-2026-08-03-taskset-ar-v080-post-ar654-plan-revalidation.md
  - reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
  - reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
  - reviews/AUDIT-2026-08-03-task-ar-655-heartbeat-expiry-consumers.md
  - reviews/REVIEW-2026-08-03-task-ar-655-heartbeat-expiry-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-deterministic-liveness-time-seams.md
  - reviews/REVIEW-2026-08-03-task-ar-655-deterministic-liveness-time-seams-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-owner-governance-clock-propagation.md
  - reviews/REVIEW-2026-08-03-task-ar-655-owner-governance-clock-propagation-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-post-green-authority-seams.md
  - reviews/REVIEW-2026-08-03-task-ar-655-post-green-authority-seams-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-projection-binding-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-current-agent-binding-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-ui-initial-state-race-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-post-repair-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-post-repair-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-full-pointer-neutral-preload-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-type-strict-pointer-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
  - reviews/INDEX.md
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
  - scripts/agent_instance_registry.py
  - src/agent_runtime/templates/project/scripts/agent_instance_registry.py
  - scripts/role_routing.py
  - src/agent_runtime/templates/project/scripts/role_routing.py
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
  - scripts/owner_governance_gate.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - scripts/worktree_lifecycle_gate.py
  - src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/doctor.py
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
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
  - tests/test_ui_design_assets.py
  - tests/test_doctor.py
  - tests/test_agent_identity_gate.py
  - tests/test_orchestrator_atomic_writes.py
  - tests/test_role_routing.py
  - tests/test_role_routing_wiring.py
  - tests/test_claim_guard.py
  - tests/test_scm_steward.py
  - tests/test_ui_console.py
  - tests/test_ui_console_e2e.py
  - tests/test_template_mirror_gate.py
  - tests/test_owner_governance_chain_parity.py
  - tests/test_regen_host_lock_if_needed.py
  - tests/test_lock_merge_driver.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
  - reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
  - reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
  - reviews/AUDIT-2026-08-03-task-ar-655-heartbeat-expiry-consumers.md
  - reviews/REVIEW-2026-08-03-task-ar-655-heartbeat-expiry-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-deterministic-liveness-time-seams.md
  - reviews/REVIEW-2026-08-03-task-ar-655-deterministic-liveness-time-seams-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-owner-governance-clock-propagation.md
  - reviews/REVIEW-2026-08-03-task-ar-655-owner-governance-clock-propagation-t3-replan.md
  - reviews/AUDIT-2026-08-03-task-ar-655-post-green-authority-seams.md
  - reviews/REVIEW-2026-08-03-task-ar-655-post-green-authority-seams-t3-replan.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-projection-binding-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-current-agent-binding-t3-replan.md
  - reviews/REVIEW-2026-08-03-task-ar-655-ui-initial-state-race-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-post-repair-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-post-repair-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-full-pointer-neutral-preload-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final.md
  - reviews/REVIEW-2026-08-03-task-ar-655-w4b-type-strict-pointer-t3-replan.md
  - reviews/W4A-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
  - reviews/INDEX.md
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
  - Claim-progress validates a committed exact-next-revision receipt and matching projection before returning success; indeterminate receipts are not blind-retry-safe.
  - Agent-instance publication is serialized and atomic, with revision and both timestamps advancing as one coherent tuple.
  - Projection without an explicit clock uses the wall clock, accepts only a live claim, and always emits agent mutation revision.
  - Role-routing overlays carry paired deadlines and revision, and support owner-checked heartbeat without entering the primary pointer.
  - Cockpit freshness rendering is null-safe before initial Runtime state load and preserves neutral, non-fabricated output.
  - Claim-progress validates the complete shared canonical pointer-agent tuple against the committed claim.
  - Canonical pointer-agent validation requires committed response-claim key presence and exact JSON type plus value equality.
  - State-derived cockpit summary and flow facts remain neutral until Runtime state exists, including delayed and failed state requests.
verification:
  - python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py tests/test_doctor.py tests/test_agent_identity_gate.py tests/test_orchestrator_atomic_writes.py tests/test_ui_design_assets.py -q
  - python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
  - python -m pytest -q
handoff: Attach the atomicity tests, owner mismatch, crash/restart, replan old/new scope digest proof, cross-consumer expiry matrix, and independent W4b.
stop_condition: Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.
verified_at: 2026-08-03T07:59:42+09:00
verified_by: le-20260803-001200-kst-ar655lease001
evidence_refs:
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803005954.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803040700.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803045245.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803054932.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803065900.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803075942.json
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
- reviews/AUDIT-2026-08-03-task-ar-655-heartbeat-expiry-consumers.md
- reviews/REVIEW-2026-08-03-task-ar-655-heartbeat-expiry-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-deterministic-liveness-time-seams.md
- reviews/REVIEW-2026-08-03-task-ar-655-deterministic-liveness-time-seams-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-owner-governance-clock-propagation.md
- reviews/REVIEW-2026-08-03-task-ar-655-owner-governance-clock-propagation-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-post-green-authority-seams.md
- reviews/REVIEW-2026-08-03-task-ar-655-post-green-authority-seams-t3-replan.md
- reviews/INDEX.md
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
- scripts/agent_instance_registry.py
- src/agent_runtime/templates/project/scripts/agent_instance_registry.py
- scripts/role_routing.py
- src/agent_runtime/templates/project/scripts/role_routing.py
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
- scripts/owner_governance_gate.py
- src/agent_runtime/templates/project/scripts/owner_governance_gate.py
- scripts/worktree_lifecycle_gate.py
- src/agent_runtime/templates/project/scripts/worktree_lifecycle_gate.py
- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/doctor.py
- agents/project/NEXT-SESSION-POINTER.yml
- agents/project/TEMPLATE-MIRROR-CONTRACT.json
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
- tests/test_ui_design_assets.py
- tests/test_doctor.py
- tests/test_agent_identity_gate.py
- tests/test_orchestrator_atomic_writes.py
- tests/test_role_routing.py
- tests/test_role_routing_wiring.py
- tests/test_claim_guard.py
- tests/test_scm_steward.py
- tests/test_ui_console.py
- tests/test_template_mirror_gate.py
- tests/test_owner_governance_chain_parity.py
- tests/test_regen_host_lock_if_needed.py
- tests/test_lock_merge_driver.py
- tests/fixtures/host/agent_runtime.lock.json
- reviews/AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries.md
- reviews/REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan.md
- reviews/REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment.md
- reviews/AUDIT-2026-08-03-task-ar-655-heartbeat-expiry-consumers.md
- reviews/REVIEW-2026-08-03-task-ar-655-heartbeat-expiry-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-deterministic-liveness-time-seams.md
- reviews/REVIEW-2026-08-03-task-ar-655-deterministic-liveness-time-seams-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-owner-governance-clock-propagation.md
- reviews/REVIEW-2026-08-03-task-ar-655-owner-governance-clock-propagation-t3-replan.md
- reviews/AUDIT-2026-08-03-task-ar-655-post-green-authority-seams.md
- reviews/REVIEW-2026-08-03-task-ar-655-post-green-authority-seams-t3-replan.md

## Scope

Unify local lifecycle timestamps without creating a remote lease service.

## Steps

1. Add expiry and concurrent-renewal negative fixtures.
2. Add RED coverage for invalid create lease and explicit reaper/watchdog grace before changing implementation.
3. Add RED coverage for low-level acquire/heartbeat TTL and overflow-safe full-sweep auditing.
4. Implement fail-closed lease/grace value domains in root/template mirrors.
5. Implement atomic owner-checked heartbeat and renewal with revision and scope bindings.
6. Wire orchestrator progress and instance/pane receipts to the same mutation.
7. Adopt one expiry classifier in registered read, cleanup, Doctor, and UI consumers.
8. Validate claim-progress receipts and serialize atomic instance publication.
9. Make default projection fail closed and direct overlay producers emit renewable paired leases without entering the primary pointer.
10. Verify crash, restart, stale projection, full-suite fixtures, and cross-surface behavior.

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
- Claim-progress accepts only a committed exact-next-revision receipt with a matching projection and marks indeterminate responses non-success and unsafe for blind retry.
- Agent-instance revision plus timestamps publish atomically under serialized authority and cannot roll back or form a torn tuple.
- Projection uses the wall clock by default, accepts only live authority, and always carries agent mutation revision.
- Role-routing overlays use paired leases and owner-checked heartbeat while remaining outside the primary pointer and scope-renew paths.
- Cockpit rendering may precede the initial Runtime state response without throwing; the neutral clock remains honest until real state arrives.
- Merge progress accepts only a complete canonical pointer-agent record whose every shared field equals the committed claim; overlays remain pointer-free.
- Before state arrival or after state-load failure, the cockpit renders no factual healthy zero, pass, idle, WIP, throughput, or cycle claims; real metrics replace the neutral state after success.

## Verification

- `python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py tests/test_doctor.py tests/test_agent_identity_gate.py tests/test_orchestrator_atomic_writes.py tests/test_ui_design_assets.py -q`
- `python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python -m pytest -q`

## Handoff

Attach the atomicity tests, owner mismatch, crash/restart, cross-consumer expiry matrix, and independent W4b.

## Stop Boundary

Stop before introducing a network lease dependency, auto-committing host state, or recovering a claim without owner identity.


## Accepted migration cost (2026-08-03, W4b round 4)

Two consequences were accepted deliberately rather than discovered later.

**Heartbeat now reads the unit spec on every beat.** Editing a unit's
`target_files` mid-flight starts refusing heartbeats until a replan-backed
`renew` lands. That is what "the lease tracks the approved scope" means: a
self-consistent claim is not an authorized claim, and heartbeat is the command
that keeps a claim alive indefinitely, so it must be anchored the same way
`renew` already is.

**A live pre-existing overlay claim is stranded, one time only.** An overlay
created before overlays carried a `scope_binding` can no longer heartbeat
(`claim scope binding is missing`). `adopt` does **not** repair it - not
because of the overlay guard, but because the spec-less branch demands an
accepted replan whose `unit_id` matches the claim, and an overlay has no
`unit_id`. `role_routing` re-dispatch will not heal it either: the idempotency
path treats a missing field as "not unexpected", matches, and no-ops. Such a
claim can only be ended once its lease expires.

Accepted rather than fixed because overlays are 30-minute, additive, and
idempotently re-created, so the window is bounded and self-clearing - and
because adding an overlay special case to `adopt` is the exact pattern that
produced two P1s in this unit. Written down here so it is a known cost rather
than a belief that `adopt` handles it.
