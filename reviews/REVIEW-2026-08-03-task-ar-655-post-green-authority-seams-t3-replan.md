---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-post-green-authority-seams-t3-replan
title: TASK-AR-655 post-GREEN authority seams T3 amendment
date: 2026-08-03
created_at: 2026-08-03T03:20:42+09:00
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
verdict: ADD_ONLY_POST_GREEN_AUTHORITY_SEAMS
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 9ef74661b9ce5ba24a51e39368579772f93a9d6a
candidate_tree: bf0123a34e5a61cb6d1db69bd0084637c4bd24c4
release_authorized: false
tags: [task-ar-655, t3-replan, receipt, registry, projection, role-routing, fixtures]
---

# TASK-AR-655 post-GREEN authority seams T3 amendment

## Decision

Accept the independent audit and extend the registered footprint only with the
root/template role-routing producer, its focused and wiring regressions, the
three historical fixture suites exposed by the shared classifier, and these
two review records. The dispatcher, orchestrator, registry, mirror contract,
installed host lock, and their primary tests are already registered.

The full-suite fixture failures do not authorize a compatibility bypass. Active
fixtures must emit the same paired deadline contract as production; the stale
fixture must emit an equal expired pair. Production default projection must use
the wall clock, not treat omitted `--now` as permission to skip liveness.

## Failure-first order

1. Commit this scope amendment, exact lookup evidence, and lifecycle update
   before adding or changing any new regression.
2. Commit a test-only RED for receipt indeterminacy, registry concurrency and
   tuple invariants, projection default liveness/revision, and role-overlay
   lease production. Include the already failing full-suite wiring witness.
3. Implement receipt validation, serialized atomic registry publication,
   unconditional projection liveness, and canonical overlay leases in the
   exact root/template pairs.
4. Update only the incomplete active/stale fixtures with paired deadlines;
   never enlarge grace or weaken the classifier.
5. Refresh mirror and installed-lock evidence, run the complete registered
   suites and complete repository suite, then create one append-only Compound
   for the five clear signatures.
6. Run worker self-check, distinct W4b, and a distinct skeptic pass. Keep the
   claim active until all three accept the same candidate identity.

## Acceptance contract

- An orchestrator zero-exit is success only with the expected heartbeat status,
  `receipt.committed is true`, exact next revision, and an identity-matched
  projection at the same revision. Otherwise it is non-success and explicitly
  not safe for blind retry.
- Registry read/merge/publication is cross-process serialized and power-loss-safe;
  the returned record equals the persisted record and never rolls back revision
  or publishes a torn timestamp tuple.
- Projection always resolves an aware evaluation time, accepts only a live
  claim, and always emits agent mutation revision.
- Active role overlays have equal top-level/nested lease deadlines and revision
  zero at creation. Owner/callsite-checked heartbeat extends the original lease
  duration and returns an explicit no-primary-pointer projection receipt;
  standalone projection and scope-renew remain refused for overlays.
- All 26 full-suite failures are closed without a grace exception, status
  exception, hidden warning, or time-seam bypass.

The active claim remains claimed and the unit remains verification-failed. No
release, version, tag, push, publish, deploy, CI dispatch, or external action is
authorized.
