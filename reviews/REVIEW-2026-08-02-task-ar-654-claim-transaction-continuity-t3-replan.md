---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-claim-transaction-continuity-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T18:04:57+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-transaction-boundary.md
  - reviews/REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan.md
tags: [task-ar-654, t3, transaction, no-clobber, rollback, checkout-activation, provenance]
---

# TASK-AR-654 claim transaction continuity T3 replan

## Why the continuity plan is refined

The prior continuity replan correctly introduced an inner/outer generation
witness and a shared lock. Its RED implementation audit then exposed a wider
transaction contract: safe authority depends on canonical identifiers,
exclusive first publication, identity-bound rollback, explicit checkout
activation, immutable release provenance, and complete overlay idempotency.

The parent candidate remains `a02547cf00185ddcb6e69f9fecfebc4090455507`
(tree `6833e622cf77ec8f17ea82da2a0a05fef042959f`). All current production
changes are uncommitted and therefore supply no candidate evidence. Every W4
result for an earlier tree remains superseded.

## Transaction contract decision

1. Validate claim IDs before deriving any artifact path. Handoff, log, claim,
   marker, and verification evidence must be direct canonical repository
   objects of the expected type and bounded size; aliases and outside paths
   fail before mutation.
2. Distinguish `pristine`, `migration-required`, `initialized`, and
   `integrity-invalid`. A valid tracked inner marker without the checkout-local
   outer anchor is `migration-required` and can become initialized only through
   explicit adoption/sync apply that copies the exact generation bytes.
3. Bind every inspection to an unchanged store and ancestor snapshot after the
   kernel lock is acquired. Marker adoption/activation verifies store entries
   again and rolls back only markers created by the current call when identity
   still matches.
4. Retain overwrite-style atomic writes for updates, but add an exclusive
   no-clobber publication API for new authority. It must use unpredictable
   exclusive sidecars, reject aliases/reparse points and non-directory parents,
   refuse a destination race without overwriting it, clean its own sidecar,
   `fsync` the file and parent directory where supported, and preserve the
   existing last-writer-wins update contract.
5. Claim create is a two-phase transaction. Preflight performs no taskset or
   artifact mutation; the locked phase revalidates authority, publishes new
   handoff/log/claim objects exclusively, establishes the witness pair, and on
   failure removes only byte-and-identity-matching objects made by that call.
   Pre-existing initialized markers are never rolled back.
6. Release updates an active claim atomically under the same lock. Inactive
   claims reject a second release before changing verifier, evidence, status,
   or timestamps. A post-commit event failure reports committed authority
   truthfully rather than pretending the release was rolled back.
7. A role overlay is idempotent only when claim metadata, identity, routing,
   parent links, persistence, direct handoff/log objects, and canonical paths
   match the entire deterministic contract. Partial matches and stale
   artifacts are collisions. Hooks and event logs run after releasing the
   authority lock.
8. Reaper mutation uses the same strict store reader and lock/snapshot
   boundary. It validates again immediately before atomic write and separates
   authoritative mutation success from later audit-hook failure.

## Failure-first and verification sequence

1. Preserve the existing RED tests in `a02547cf`, then add exact negatives for
   the ten signatures recorded by the triggering audit.
2. Implement the shared claim-store module, secure atomic create API,
   dispatcher/release transaction, role overlay, reaper, closeout, sync,
   adoption, doctor, and lock integrations with source/template parity.
3. Exercise first/second artifact failure, claim failure, inner/outer marker
   failure, retry, pre-existing initialized markers, stale snapshots, ancestor
   aliases, destination races, partial overlays, inactive re-release, and
   post-commit hook failures.
4. Keep native Windows junction, `msvcrt` process-lock, atomic publication,
   reaper concurrency, and dispatcher rollback/re-release cases in the
   `windows-latest` Python 3.10/3.11/3.12 workflow. Local non-Windows skips do
   not satisfy the release prerequisite.
5. Run affected suites, registered verification, full Runtime suite,
   source/template parity, host lock, asset, Compound, schema, state-sync, and
   owner-governance gates on one candidate.
6. Create fresh machine Verify evidence and one append-only Compound covering
   both the eight still-unrecorded continuity/component signatures and the ten
   transaction signatures. Preserve all prior records byte-for-byte.
7. Commit the exact candidate, perform W4a, then use distinct fresh agents for
   W4b and skeptic review. Any P1 creates a new candidate and invalidates the
   sequence.

## Scope amendment

The authorized implementation scope additionally names:

- `scripts/atomic_io.py` and its packaged mirror;
- dispatcher, role-routing, reaper, closeout, claim guard, parallel gate, and
  work source/template pairs;
- `agent_runtime.claim_store`, sync, adoption, doctor, and lock integration;
- focused claim-store, atomic-I/O, dispatcher, role, reaper, sync, Windows,
  and Autofolio host-contract regressions;
- `.github/workflows/test.yml`, template-mirror metadata, and the generated
  fixture host lock; and
- task, unit, claim, handoff/log, review, Verify, append-only Compound, and
  generated evidence indexes required by this lifecycle.

This refinement does not authorize archive-aware Scribe migration, TASK-AR-655
heartbeat implementation, advisory UI convergence, consumer repository
mutation, or release execution. Those remain separate work and/or release
gates.

## Stop and release boundary

Native Windows evidence is still absent until the approved workflow executes
externally. The implementation may become a locally verified candidate, but
the claim must not be released and the version must not be published on local
or modeled evidence alone.

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deployment, CI dispatch, or external release action is authorized.
