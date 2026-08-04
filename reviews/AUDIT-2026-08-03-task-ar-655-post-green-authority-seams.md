---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-03-task-ar-655-post-green-authority-seams
title: TASK-AR-655 post-GREEN receipt, registry, projection, and producer audit
date: 2026-08-03
created_at: 2026-08-03T03:20:42+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: audit
reviewer: codex-ar655-liveness-cross-slice-reviewer-20260803
reviewer_role: peer-reviewer
status: completed
signal: fail
verdict: REVISE_RECEIPT_REGISTRY_PROJECTION_AND_OVERLAY_AUTHORITY
priority: P1
finding_counts: {P0: 0, P1: 4, P2: 1}
candidate_commit: 9ef74661b9ce5ba24a51e39368579772f93a9d6a
candidate_tree: bf0123a34e5a61cb6d1db69bd0084637c4bd24c4
release_authorized: false
tags: [task-ar-655, heartbeat, receipt, registry, projection, role-routing, full-suite]
---

# TASK-AR-655 post-GREEN authority seam audit

## Outcome

The registered liveness suites, mirror contract, installed lock, and nested
owner-governance journey were GREEN, but an independent cross-slice audit and
the complete repository suite found four P1 authority gaps and one P2 tuple
invariant gap. The implementation candidate must not be committed as GREEN
until these findings have their own test-only RED baseline and repair.

The complete suite result was `26 failed, 4460 passed, 11 skipped`. Twenty-five
failures were historical active-claim fixtures that omitted the newly canonical
paired deadline or used an already expired fixed date: 21 claim-transaction
fixtures, two SCM-steward fixtures, and two office-map fixtures. Those fixtures
must model the canonical paired deadline explicitly. The remaining failure was
a real producer-to-consumer gap: role-routing overlay claims were emitted
without any lease deadline and were therefore indeterminate at the canonical
parallel gate.

## P1 findings

1. `agent_orchestrator claim-progress` returns exit zero when a zero-exit
   dispatcher response is malformed, non-object, or lacks a verifiable commit
   receipt. A caller can therefore skip reconciliation even though commit state
   and retry safety are unknown.
2. `agent_instance_registry` performs an unlocked read/merge/plain-write after
   claim commit. A forced valid interleaving lets revision 1 overwrite an
   already published revision 2 while both calls report success.
3. `task_claim_dispatcher projection` evaluates liveness only when `--now` is
   supplied and omits the agent mutation revision on the default path. Normal
   callers omit `--now`, so an expired or indeterminate claim can be projected.
4. `role_routing` emits active overlay claims without `expires_at` and
   `lease.expires_at`. The canonical liveness classifier correctly treats those
   claims as indeterminate, making the high-risk release-to-review chain fail at
   its first consumer.

## P2 finding

The registry merges revision and timestamps independently. Equal revisions can
advance timestamps, and a higher revision with one older and one newer
timestamp can publish a hybrid tuple that never existed in any claim.

## Exact Compound lookup

The failure-to-regression lookup was run before repair. Every exact search was
clear (`[]`):

- `defect:agent-orchestrator-claim-progress-acknowledges-s:865827031e86d0ca`
- `defect:agent-instance-registry-concurrent-publish-rolls:609cd581edd3cea9`
- `defect:claim-projection-without-explicit-now-skips-live:f96238afdd1aa3f9`
- `defect:role-routing-overlay-claim-omits-lease-deadline:01470e887b26aa2b`
- `defect:agent-instance-registry-mixes-revision-timestamp:1997c0b1b3471da3`

These signatures require one append-only Compound record after GREEN; no prior
record may be edited.

## Required RED matrix

- Orchestrator: zero-exit malformed/non-object/incomplete/incoherent receipts
  return bounded `claim_progress_receipt_indeterminate`, exit 2,
  `commit_state=unknown`, and `retry_safe=false`; a valid committed warning
  receipt passes through exactly once.
- Registry: deterministic concurrent publication cannot roll back a newer
  revision; lower revisions are ignored, equal revisions are exact-idempotent
  only, and higher revisions update one validated timestamp tuple atomically.
- Projection: omitted `--now` calls the wall-clock seam, refuses expired and
  indeterminate claims, and always includes the current agent mutation revision.
- Role routing: every newly active overlay carries equal top-level and nested
  deadlines and a revision, supports owner-checked heartbeat without entering
  the primary pointer, and the existing high-risk wiring test is accepted
  immediately by the canonical parallel gate.
- Full-suite fixtures: active fixtures carry equal paired deadlines; the stale
  SCM fixture carries an equal expired pair. No liveness exception or grace
  enlargement is permitted.

## Safety boundary

Claim commit remains authoritative if a post-commit registry or event stage
fails; callers receive a warning and must not retry the claim mutation blindly.
An overlay uses the same default creation lease and owner/callsite heartbeat
extension as a worker claim. Overlay heartbeat advances its revision and emits
an explicit no-primary-pointer projection receipt; standalone primary
projection and scope-renew remain refused for overlays. This avoids both an
immortal review claim and a finite but unrenewable review claim.
No network lease service, Git host-state auto-commit, release, version, tag,
push, publish, deploy, CI dispatch, external message, or consumer-repository
mutation is authorized.
