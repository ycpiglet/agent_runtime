---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-lease-grace-bounds-t3-replan
title: TASK-AR-655 lease and grace bounds T3 scope amendment
date: 2026-08-03
created_at: 2026-08-03T00:30:23+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: AMEND_BOUNDED_SCOPE_AND_PROCEED_RED_FIRST
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 905480cefa4775141e304eda4ca8c20b6b8ff60c
candidate_tree: 58aa45a32d3033e54542111ecd0664b36a75c175
release_authorized: false
tags: [task-ar-655, t3-replan, scope-amendment, lease, grace, red-first]
---

# TASK-AR-655 lease and grace bounds T3 scope amendment

## Decision

Accept the adjacent defect routed from the final AR-654 audit into the already
planned and now claimed TASK-AR-655:

`defect:negative-lease-or-grace-kills-live-claim:315a2daf2bae5424`

`defect:claim-reaper-deadline-overflow-partially-mutates:5d3658dc71ab217a`

This amendment adds only the missing lease/grace authority surfaces and their
regressions to the existing atomic heartbeat/renewal task. It does not absorb
TASK-AR-657 verifier authenticity, TASK-AR-651 portable release work, native
Windows evidence, or Scribe closure debt.

## Authorized implementation and verification footprint

- `scripts/task_claim_dispatcher.py`
- `src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`
- `scripts/claim_lease.py`
- `src/agent_runtime/templates/project/scripts/claim_lease.py`
- `scripts/claim_reaper.py`
- `src/agent_runtime/templates/project/scripts/claim_reaper.py`
- `scripts/deadlock_watchdog.py`
- `src/agent_runtime/templates/project/scripts/deadlock_watchdog.py`
- `tests/test_task_claim_dispatcher.py`
- `tests/test_claim_lease.py`
- `tests/test_claim_reaper.py`
- `tests/test_deadlock_watchdog.py`
- `tests/test_claim_reaper_concurrency.py`
- `tests/test_claim_reaper_hook.py`
- `tests/test_template_mirror_gate.py`
- `tests/test_regen_host_lock_if_needed.py`
- `tests/test_lock_merge_driver.py`
- `tests/fixtures/host/agent_runtime.lock.json`

The unit also registers the missing root mirrors for its existing
state-sync, parallel-worktree, and worktree-lifecycle template targets. The
template-only `agent_orchestrator.py` has no root counterpart and remains
correctly template-only.

## Required sequence

1. Keep the exact Compound lookup result (`[]`) attached to task, unit, and
   claim authority.
2. Add RED tests for create `-1` and `0`, create overflow, low-level acquire
   and heartbeat TTL bounds, future-live reaper mutation with negative explicit
   grace, watchdog upfront rejection, API `bool` rejection, zero grace,
   one-minute lease, environment normalization, huge nonnegative grace, and a
   maximum-deadline claim following a reapable claim in one sweep.
3. Run only the new focused tests and record their expected failures before
   changing implementation.
4. Implement shared fail-closed validators at every public CLI/API boundary,
   keeping root/template mirrors identical. Watchdog validation happens before
   either watchdog step runs.
5. Re-run focused, concurrency/hook, template, host-lock, and full Runtime
   verification. Regenerate the host lock only through its provided generator.
6. After fresh Verify is green, create one append-only Compound that covers the
   exact defect signature and links the actual RED regressions. Do not rewrite
   earlier Compound records.
7. Continue the original atomic heartbeat/renewal acceptance, then run W4a,
   a distinct W4b, and a distinct skeptic review against exact commits.

## Compatibility and stop boundary

- Lease minutes: plain integer, minimum `1`; `bool`, zero, negative, and
  datetime overflow are refused before mutation.
- Low-level lease TTL seconds: plain integer, minimum `1`, at both acquire and
  heartbeat; invalid or overflowing values are refused before mutation.
- Explicit grace seconds: plain integer, minimum `0`; `bool`, float, string,
  and negative are refused before mutation.
- Zero/equality and negative-environment legacy behavior remain compatible as
  documented by the audit.
- Huge nonnegative grace is handled with overflow-safe integer comparison and
  biases toward retaining a claim; near-maximum deadlines cannot split a sweep
  from its queued audit records.

Stop before a network lease service, implicit scope broadening, host-state
autocommit, cross-owner recovery, consumer writes, CI dispatch, version bump,
tag, push, publish, deployment, claim release, or external release.

`release_authorized` remains false.
