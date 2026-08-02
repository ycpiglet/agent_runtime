---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-combined-green-precommit
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-precommit-audit
reviewer: codex-task-ar-654-combined-precheck-group
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 7, P2: 3}
baseline_commit: d547123070d47e543cea2456ef109f9da6f79cf9
baseline_tree: df3e13c0348a37faa4fe55906f2aa78991afb743
candidate_kind: uncommitted-working-tree
release_authorized: false
created_at: 2026-08-02T19:21:52+09:00
tags: [task-ar-654, precommit, post-commit, projection, marker-rollback, w4b, lease, release-cascade]
---

# TASK-AR-654 combined-green precommit audit

## Verdict

`REVISE — P0: 0, P1: 7, P2: 3.`

The combined dirty candidate passed `1561 passed, 8 skipped` in the affected
integration matrix and `4230 passed, 11 skipped` in the complete local suite.
Three fresh read-only reviews nevertheless reproduced remaining transaction
truth gaps and adjacent release blockers. The green suite is a useful baseline
but is superseded for release purposes.

## Current TASK-AR-654 findings

1. **P1 — closeout projection false failure.** `work close` persists completed
   frontmatter and its closeout block before refreshing generated views. A
   projection `OSError` is then reported as an active-claim context failure even
   though durable closeout already committed.
2. **P1 — sync false success.** Sync can observe `template_application=not-applied`,
   `applied=0`, and remaining updates yet return exit zero because its final
   condition checks conflicts and store integrity but not observed application.
3. **P1 — opt-in SCM persistence false failure.** Claim create persists its
   authority before calling the best-effort SCM helper. An exception at that
   call boundary escapes and reports create failure after the claim exists.
4. **P1 — incomplete marker rollback deletes its witness.** If the inner marker
   commits, the outer marker fails, and inner cleanup also fails, dispatcher or
   role rollback still deletes the witness claim and leaves the store
   integrity-invalid with no recovery witness.
5. **P2 — dispatcher projection is stale.** Projection uses unlocked raw claim
   reads; a concurrent release can produce an emitted active pointer for an
   already released claim.
6. **P2 — W0 inflight summary mixes snapshots.** `work status` now reads active
   rows canonically, but `inflight_overlay` builds its claim index from a
   separate unlocked plain-JSON pass, so one response may contradict itself.

These findings refine already registered signatures: post-commit durable-result
truth, marker activation partial authority, sync committed-state reporting,
complete claim snapshots, and canonical W0 integrity. They do not create new
TASK-AR-654 signatures.

## Adjacent next-release blockers

1. **P1 — W4b approval authenticity (TASK-AR-657).** Release accepts an invented
   verifier plus an unrelated repository file because it proves only string
   inequality and path existence, not a bounded canonical approval bound to the
   claim and exact candidate.
2. **P1 — lease/grace bounds (TASK-AR-655).** Negative lease creates an already
   expired claim, and negative reaper grace can classify a future-expiry live
   claim as dead.
3. **P1 — portable version cascade (TASK-AR-651).** The new portable
   `scripts/agent_runtime` package version is omitted by cascade, pending, and
   release execution checks, allowing package/template version split.
4. **P2 — portable package evidence (TASK-AR-651).** Wheel/publish/tag gates do
   not explicitly require the new claim-store and role-routing portable assets.

Exact canonical prior-knowledge search returned `[]` for:

- `defect:claim-release-accepts-invented-verifier-and-unre:e56e560c3b6a0990`;
- `defect:negative-lease-or-grace-kills-live-claim:315a2daf2bae5424`;
- `defect:portable-runtime-version-escapes-release-cascade:61d54bd7538fef11`;
- `defect:release-package-gate-omits-portable-claim-author:e018f7f057e0a6ba`.

They are intake obligations for their existing planned tasks, not authority to
edit those task scopes from the active TASK-AR-654 worker claim. TASK-AR-651
already depends on TASK-AR-655 and TASK-AR-657, so all remain release blockers.

## Required disposition

Within TASK-AR-654, add RED tests and repair closeout post-commit reporting,
sync exit truth, best-effort SCM exception isolation, marker-aware witness
rollback, canonical dispatcher projection, and one-snapshot W0 inflight data.
Then rerun the focused and full suites before implementation commit and Verify.

Route the four adjacent signatures into the named planned tasks when each is
claimed. Do not claim TASK-AR-654, local tests, or Compound coverage solves
those release blockers.

## Safety boundary

No CI dispatch, version bump, tag, publication, push, deployment, consumer
mutation, or external release action is authorized.
