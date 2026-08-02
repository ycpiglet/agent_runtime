---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-655
display_id: TASK-AR-655
task_uid: de3c2768-cf2b-4fc5-aad6-160071e91f3e
work_id: TASK-AR-655
work_uid: de3c2768-cf2b-4fc5-aad6-160071e91f3e
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-03T07:45:51+09:00
started_at: 2026-08-03T00:26:51+09:00
title: Add atomic heartbeat and renewal to task claims
status: in_progress
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-655/UNIT-TASK-AR-655-001.md
reservation_id: RES-20260730-112500-842c7890-04
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
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
review_refs:
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
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260803-002651-task-ar-655-5f27.json
summary: Keep long-running task claims truthful and make expiry consistent across claim, pointer, Doctor, state sync, and UI.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - task_claim_dispatcher exposes atomic owner-checked heartbeat and renew commands.
  - Heartbeat updates claim top-level and nested lease timestamps together.
  - Wrong owner, expired claim, timestamp regression, and concurrent renewal fail closed.
  - A replan-aware renewal binds the current task, unit, target-file, and stop-boundary digests without silently broadening the prior claim.
  - Doctor, state sync, worktree lifecycle, and UI use one expiry interpretation.
  - Progress updates cannot leave an active pointer paired with an expired claim.
  - Create refuses non-integer, boolean, zero, negative, and overflowing lease durations before persistence.
  - Low-level lease acquire and heartbeat reject boolean, nonpositive, and overflowing TTL values before mutation.
  - Explicit reaper and watchdog grace rejects non-integer, boolean, and negative values before either watchdog step or any claim mutation.
  - Zero grace, one-minute lease, positive equality, and negative-environment normalization remain backward compatible.
  - Huge nonnegative grace is overflow-safe and conservatively retains live authority.
  - Reaper deadline comparison cannot partially mutate a sweep and then lose its queued audit records on datetime overflow.
  - Claim-progress acknowledges success only after validating a committed exact-next-revision receipt and matching projection; indeterminate receipts are non-success and unsafe to retry blindly.
  - Agent-instance publication is serialized and atomic, and revision plus timestamps advance as one coherent tuple.
  - Projection without an explicit clock uses the wall clock, accepts only a live claim, and always emits agent mutation revision.
  - Role-routing overlays and active fixtures carry equal top-level and nested lease deadlines without widening grace.
  - Cockpit freshness rendering tolerates a pre-load null Runtime state without fabricating freshness or failing the browser layout flow.
  - Claim-progress binds the complete shared canonical pointer-agent tuple, not a partial current-agent subset.
  - Canonical pointer-agent comparison is JSON-type-strict and cannot launder absent response-claim members through null.
  - Pre-load cockpit summary and flow surfaces remain neutral and never fabricate healthy zero, pass, idle, or WIP facts.
verification:
  - python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py tests/test_doctor.py tests/test_agent_identity_gate.py tests/test_orchestrator_atomic_writes.py tests/test_ui_design_assets.py -q
  - python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
  - python -m pytest -q
---

# TASK-AR-655 - Add atomic heartbeat and renewal to task claims

## Goal

- Keep long-running task claims truthful and make expiry consistent across claim, pointer, Doctor, state sync, and UI.

## Scope

- Add owner-checked task claim heartbeat/renew, wire progress updates to it, and reconcile expired active claims across every consumer.
- Fail closed on invalid create lease and explicit reaper/watchdog grace before authority persistence or mutation, while preserving the documented zero and environment compatibility boundaries.
- Validate post-commit receipts, serialize instance projections, close default projection liveness, and make direct overlay producers emit the same canonical lease authority.

## Acceptance Criteria

- task_claim_dispatcher exposes atomic owner-checked heartbeat and renew commands.
- Heartbeat updates claim top-level and nested lease timestamps together.
- Wrong owner, expired claim, timestamp regression, and concurrent renewal fail closed.
- A replan-aware renewal binds the current task, unit, target-file, and stop-boundary digests without silently broadening the prior claim.
- Doctor, state sync, worktree lifecycle, and UI use one expiry interpretation.
- Progress updates cannot leave an active pointer paired with an expired claim.
- Create accepts only a plain integer lease of at least one minute and refuses overflow without residue or traceback.
- Low-level lease acquire and heartbeat accept only a plain integer TTL of at least one second and refuse overflow before mutation.
- Reaper and watchdog accept only a plain integer explicit grace of at least zero, validate before watchdog execution, and handle huge nonnegative grace without datetime overflow.
- Zero grace, one-minute lease, inclusive equality, and negative-environment normalization are locked by regressions.
- Deadline/grace comparison is overflow-safe before and after earlier claims in the same sweep, preserving its audit trail.
- Claim-progress returns success only for a committed exact-next-revision receipt with a matching claim projection; an indeterminate zero-exit response is non-success and not blind-retry-safe.
- Agent-instance revision and timestamps are published atomically under serialized authority and cannot roll back or form a tuple absent from a claim.
- Projection evaluates the wall clock when `--now` is omitted, accepts only live claims, and always includes the current agent mutation revision.
- Role-routing overlays and test fixtures use equal top-level and nested lease deadlines; no consumer gets a grace or status bypass.
- Cockpit rendering before the initial Runtime state response remains neutral and null-safe, then preserves built-at freshness semantics after state arrival.
- Claim-progress validates every field in the shared canonical pointer-agent tuple against the committed claim while preserving pointer-free overlays.
- Canonical pointer-agent validation requires response-claim key presence and exact JSON type plus value equality; booleans, integers, floats, and absent/null values cannot alias.
- Before Runtime state exists, the cockpit hides or marks unavailable every state-derived summary and flow fact; delayed or failed state requests never appear healthy.

## Verification

- `python -m pytest tests/test_claim_store.py tests/test_task_claim_dispatcher.py tests/test_claim_lease.py tests/test_claim_reaper.py tests/test_deadlock_watchdog.py tests/test_claim_reaper_concurrency.py tests/test_claim_reaper_hook.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_worktree_lifecycle_gate.py tests/test_ui_state.py tests/test_doctor.py tests/test_agent_identity_gate.py tests/test_orchestrator_atomic_writes.py tests/test_ui_design_assets.py -q`
- `python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python -m pytest -q`
