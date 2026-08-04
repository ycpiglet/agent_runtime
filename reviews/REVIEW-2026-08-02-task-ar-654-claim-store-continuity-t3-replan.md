---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-claim-store-continuity-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T14:52:33+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-authority-continuity-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final.md
tags: [task-ar-654, t3, claim-store, continuity, status-authority, bounded-json, windows-ci]
---

# TASK-AR-654 claim-store continuity T3 replan

## Why the component candidate is superseded

Production candidate `2f4ec606ad460efd556780c905240b26571c1986`
(tree `5dc072f194adedc024e98eb2259bbc0a1459931f`) correctly rejects the
previously known component aliases and availability failures. Fixture-only
commit `5bdd3ef1f2b38ffa4e26f4a0133720a6faf20785` changes no production code.
Two fresh independent audits nevertheless proved three remaining classes:

1. dispatcher-normalized active status such as `" CLAIMED "` is silently
   ignored by closure, and an unknown status is also treated as inactive;
2. a populated direct `task_claims` directory can be moved aside and replaced
   with a new direct empty directory, erasing remembered authority while all
   component checks still pass; and
3. deeply nested or integer-limit claim JSON escapes bounded handling, while
   native Windows junction behavior and deterministic enumeration failures
   still lack release-grade evidence.

The first two defects produced successful actual `work close` mutation without
the hidden repeated-failure authority. The JSON defects remained fail-closed
but emitted tracebacks. The candidate is rejected, verification remains
failed, and no earlier W4 or machine result authorizes closure.

## Prior-knowledge search

Exact canonical `--no-legacy --json` searches returned `[]` for all three new
stable signatures:

- `claim status casing hides active repeated failure` ->
  `defect:claim-status-casing-hides-active-repeated-failur:43313896c2b45087`;
- `direct claim store replacement hides canonical authority` ->
  `defect:direct-claim-store-replacement-hides-canonical-a:7477bae20f4a3c1f`;
- `deep active claim JSON escapes bounded handling` ->
  `defect:deep-active-claim-json-escapes-bounded-handling:6694294b2602e0ce`.

No Compound is created during replanning. The next append-only record must be
created only after all unresolved component and continuity signatures have a
complete prevention matrix and fresh Verify evidence.

## Continuity contract decision

Introduce a small shared `agent_runtime.claim_store` module with three-way
source/host/template parity. An initialized store carries one immutable,
canonical, bounded JSON witness at each end:

- an outer anchor in the current checkout's Git administration directory at
  `agent-runtime/task-claim-store` (or a root-local fallback for a non-Git
  host); and
- an inner member at `agents/runtime/task_claims/.claim-store`.

The identical payload contains only schema, a UUIDv4 generation ID, and a
retained canonical `witness_claim_id`. Neither marker uses a `.json` suffix,
so existing `task_claims/*.json` readers cannot mistake it for a claim.

The checkout-specific Git administration directory is deliberate: it is
outside the replaceable working-tree trust boundary, survives reset/clean and
replacement of all `agents/runtime`, and does not incorrectly pair distinct
linked-worktree claim stores with one common anchor.

State is valid only as follows:

- both markers absent plus an absent or truly empty direct final store is
  `pristine` and remains compatible;
- a non-empty markerless store is `migration-required`, never silently empty;
- both direct regular bounded markers must be byte-identical, schema-valid,
  and name one retained direct canonical claim in the same store;
- one-sided, mismatched, malformed, oversized, aliased, unavailable, missing-
  witness, or initialized-empty state is integrity-invalid and fail-closed.

The module supplies a bounded kernel advisory lock (POSIX `flock`, Windows
`msvcrt`, five-second timeout), component/Windows-reparse validation, store
inspection, pre/post identity snapshots, explicit legacy adoption, first-claim
initialization, and unchanged-snapshot verification. Locks are checkout-local
and automatically released by the OS on process exit. No marker is packaged
as a static template or included in managed-template digests.

## Failure-first implementation sequence

1. Add RED tests before production code for mixed-case active status, unknown
   and non-string status, deep nesting, integer-limit values, exact and over-
   limit payloads, deterministic `scandir` open/iteration failures, direct
   populated-store replacement, and a swap during enumeration.
2. Add a dedicated witness test matrix for pristine, migration-required,
   initialized, partial, mismatch, malformed, oversized, lost witness,
   replacement, lock contention/timeout, linked-worktree isolation, crash
   interruption, idempotence, and strict non-overwrite behavior.
3. Make status parsing match dispatcher normalization with a closed known
   inactive vocabulary. Unknown and non-string values are integrity failures.
4. Read claim JSON with a `256 KiB` cap plus one sentinel byte, strict UTF-8,
   and bounded handling for `OSError`, Unicode errors, `JSONDecodeError`,
   `RecursionError`, and integer-limit `ValueError`.
5. Hold the store lock across actual `work close` authority resolution through
   its first canonical work mutation. Claim creation and overlay creation use
   the same lock, atomically persist a claim before establishing inner then
   outer immutable witnesses, and refuse to bless an outer-only replacement.
   Release writes become atomic; other status mutation paths are either placed
   under the lock now or explicitly carried into TASK-AR-655.
6. `sync/update --check`, diff, reconcile, and adoption remain read-only and
   expose the witness state. `sync/update --apply` migrates a safe legacy
   populated store before copying the new closure code, refuses invalid state
   without template writes, then rechecks and writes the host lock. Doctor
   diagnoses every state and must not auto-repair an ambiguous partial pair.
7. Extend crash-safe claim persistence and parallel-transaction allowlists only
   for the exact inner marker path; the Git-admin outer anchor is local runtime
   state and is never staged. Preserve arbitrary-path refusal.
8. Add Windows-only actual-close tests for live and broken `mklink /J`
   junctions with non-destructive `rmdir` cleanup, and add a targeted
   `windows-latest` Python 3.10/3.11/3.12 CI job. Local non-Windows runs may
   skip these cases; native CI evidence remains a release prerequisite.
9. Keep all source/template scripts byte-identical where registered, update the
   asset/profile/mirror contracts, regenerate the fixture host lock, and align
   only central test helpers that intentionally create valid initialized
   stores. Markerless-populated RED fixtures remain explicit.
10. Run focused RED-to-green evidence, all affected test files, the registered
    suite, complete Runtime suite, asset/mirror/lock/Compound/work-schema/owner
    gates, and a fresh machine Verify on one exact candidate.
11. Append one new Compound linking both work IDs and all still-unrecorded
    signatures: broken ancestor, Windows junction, unreadable enumeration,
    missing intermediate parent, entry loop, status normalization, direct
    replacement, and bounded claim JSON. Then require entirely fresh W4a,
    distinct W4b, and skeptic review.

## Scope amendment

Production scope is expanded only as required by the authority boundary:

- the new three-way claim-store module;
- closure, work-close, dispatcher/release, overlay writer, reaper where needed,
  claim persistence, sync/update/adoption/doctor integration;
- exact runtime asset/profile/mirror/lock metadata;
- affected focused tests and `.github/workflows/test.yml`.

Advisory UI/read-model scanners may remain on their current API only if they
cannot authorize mutation; convergence of all advisory readers is follow-up
work. Scribe archive migration remains a separate P1 task. This replan does
not authorize consumer repository changes or release execution.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deployment, CI dispatch, or external release action is authorized.
