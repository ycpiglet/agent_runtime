---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-claim-transaction-boundary
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: orchestrator-audit
reviewer: codex-root-task-ar-654-orchestrator
reviewer_role: lead-engineer
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 5, P2: 2}
candidate_commit: a02547cf00185ddcb6e69f9fecfebc4090455507
candidate_tree: 6833e622cf77ec8f17ea82da2a0a05fef042959f
release_authorized: false
created_at: 2026-08-02T18:04:57+09:00
tags: [task-ar-654, transaction, publication, rollback, checkout-activation, role-overlay, revise]
---

# TASK-AR-654 claim transaction-boundary audit

## Verdict

`REVISE — P0: 0, P1: 5, P2: 2.`

The failure-first candidate at `a02547cf` correctly exposes the durable
claim-store continuity boundary, but pre-implementation contract review and
the resulting RED matrix show that witness continuity alone is insufficient.
New authority files can still escape their canonical namespace, appear
partially after an interrupted transaction, or be mistaken for an idempotent
prior operation. No implementation candidate or earlier W4 result covers
these transaction semantics.

This audit records contract findings only. The implementation remains an
uncommitted working-tree candidate and is not treated as evidence.

## P1 findings

1. **Canonical artifact authority is incomplete.** A noncanonical claim ID,
   derived handoff/log path, or aliased/out-of-repository verification
   evidence can cross the claim transaction boundary unless all identifiers
   and evidence paths are validated before side effects.
2. **Checkout activation can silently rebind a tracked inner witness.** A
   fresh clone or newly linked worktree can contain the tracked inner marker
   without its checkout-local outer anchor. Treating that state as ordinary
   initialized or pristine loses the original generation boundary.
3. **Snapshots and marker activation are not one transaction.** Replacing an
   ancestor, changing store entries after inspection, or failing the second
   marker write can approve a stale baseline or leave partial authority.
4. **Create and release transitions lack full provenance preservation.** A
   second-artifact, claim, or outer-marker failure can leave retry-blocking
   residue; re-releasing an inactive claim can overwrite the verifier and
   evidence that authorized the first transition.
5. **Role overlay idempotency is under-specified.** Matching only part of an
   existing overlay permits incomplete or stale claim/handoff/log state to be
   accepted as the requested operation instead of refusing the collision.

## P2 findings

1. Predictable atomic sidecar names and replace-style publication do not
   provide a no-clobber create primitive. Parent aliases, destination races,
   cleanup, and parent-directory durability need explicit contracts.
2. Mutation may be durable while post-commit event/audit emission fails. The
   CLI must report the committed authority truthfully and must not hold the
   claim-store lock while running non-authoritative hooks.

## Stable signatures and prior knowledge

Exact canonical `compound_record search --no-legacy --json` lookup returned
`[]` for each signature below:

- `defect:claim-id-escapes-canonical-artifact-namespace:84dd007e34346fae`;
- `defect:claim-evidence-alias-escapes-repository-boundary:422a442d426e3c59`;
- `defect:tracked-inner-marker-activates-without-checkout:7eaad2998875a161`;
- `defect:claim-store-snapshot-accepts-stale-or-aliased-ba:165eeaa33e9e0650`;
- `defect:claim-store-marker-activation-leaves-partial-aut:4d351ca878f09963`;
- `defect:atomic-no-clobber-publication-accepts-destinatio:b5af68a325007016`;
- `defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4`;
- `defect:claim-create-failure-leaves-partial-transaction:36409fe931d01cfd`;
- `defect:inactive-claim-re-release-rebinds-verification-p:da793d1a17eecca2`;
- `defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4`.

No Compound is created by this audit. The existing three TASK-AR-654 records
remain immutable. A new append-only record may be created only after the
prevention matrix and fresh machine Verify exist.

## Required disposition

Keep the claim and unit open. Replan the transaction boundary, preserve the
failure-first tests, implement exclusive publication and identity-bound
rollback, rerun the full suite and governance gates, then create fresh Verify
and Compound evidence. Review the resulting exact commit through a new W4a,
distinct W4b, and fresh skeptic pass. Native Windows execution remains a
release prerequisite, not something Linux-modeled tests can satisfy.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer-repository mutation, version bump,
tag, publication, push, deployment, CI dispatch, or external release action
is authorized.
