---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-claim-transaction-compound-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-02T20:00:07+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/REVIEW-2026-08-02-task-ar-654-postcommit-projection-t3-replan.md
tags: [task-ar-654, compound, append-only, claim-store, transaction-truth]
---

# TASK-AR-654 claim-transaction Compound scope amendment

## Decision

Register the following newly generated append-only prevention record for both
TASK-AR-654 and UNIT-TASK-AR-654-001:

`agents/project/knowledge/compounds/records/COMPOUND-20260802-195951-bind-claim-authority-to-one-durable-no-clobber-t-3b8cec108077.json`

The record was created only after failure-first regressions and the fresh
machine Verify passed. Its SHA-256 is
`acbf130685bde2327d531c6ec203233248e3c91dc87b4e7820217100becb23bd`.
The implementation authority is commit
`19362133d2dffc91647b23beab8f01956a403f7f`, tree
`9fe64b8044cc0769bd9d81cb234742907b200e0a`.

## Exact authority carried

The new record links both work IDs and exactly these 26 previously uncovered
stable defect signatures:

- `defect:broken-ancestor-symlink-hides-canonical-active-c:23158c0595f498bb`;
- `defect:windows-junction-parent-hides-canonical-active-c:731de644205f5d8d`;
- `defect:unreadable-active-claim-store-enumerates-as-empt:c7816e3946c29101`;
- `defect:missing-intermediate-claim-store-parent-hides-ac:4560560004a1fb77`;
- `defect:active-claim-symlink-loop-escapes-bounded-handli:49bf17a5e1901460`;
- `defect:claim-status-casing-hides-active-repeated-failur:43313896c2b45087`;
- `defect:direct-claim-store-replacement-hides-canonical-a:7477bae20f4a3c1f`;
- `defect:deep-active-claim-json-escapes-bounded-handling:6694294b2602e0ce`;
- `defect:claim-id-escapes-canonical-artifact-namespace:84dd007e34346fae`;
- `defect:claim-evidence-alias-escapes-repository-boundary:422a442d426e3c59`;
- `defect:tracked-inner-marker-activates-without-checkout:7eaad2998875a161`;
- `defect:claim-store-snapshot-accepts-stale-or-aliased-ba:165eeaa33e9e0650`;
- `defect:claim-store-marker-activation-leaves-partial-aut:4d351ca878f09963`;
- `defect:atomic-no-clobber-publication-accepts-destinatio:b5af68a325007016`;
- `defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4`;
- `defect:claim-create-failure-leaves-partial-transaction:36409fe931d01cfd`;
- `defect:inactive-claim-re-release-rebinds-verification-p:da793d1a17eecca2`;
- `defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4`;
- `defect:atomic-publisher-reports-failure-after-committed:2e080352410acda0`;
- `defect:role-overlay-rollback-deletes-replacement-artifa:24910ed49f07f9b7`;
- `defect:claim-store-witness-accepts-unknown-claim-status:8e42ea5ea2d844c9`;
- `defect:partial-compound-coverage-satisfies-declared-def:90587dadec03fe8f`;
- `defect:claim-json-accepts-nonfinite-or-duplicate-fields:2fc824544a55622d`;
- `defect:sync-reports-zero-after-committed-claim-migratio:4317243460108472`;
- `defect:post-commit-fallible-step-reverses-durable-autho:cb20f7de91cd1390`;
- `defect:work-status-hides-active-claim-integrity-failure:f48114a15d1fee23`.

The ordered task, unit, and active-claim signature lists remain identical.
Their newline-terminated, lexicographically sorted canonical SHA-256 is
`924f5d57931d391b49e9a5fd85efe2f70b66326070a13ea331a02963ac99b09a`.
Together with the three prior linked records, the new record must make the
set difference between registered signatures and valid Compound coverage
empty; the generated index is only a derived projection of those immutable
records.

## Prevention and verification authority

The prevention boundary is a marker-activated canonical claim store with
bounded strict JSON, locked complete snapshots, identity-bound no-clobber
publication and rollback, immutable release provenance, witness-preserving
recovery, truthful post-commit warnings and sync exits, and single-snapshot
projections. The record links the failure-first regression suites for claim
store, atomic publication, dispatcher, role routing, reaper concurrency,
closure, Compound coverage, sync, lifecycle defaults, inflight overlay, and
work close.

Fresh machine evidence is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json`, SHA-256
`078b8e4d6779f233c68647ae693e6541df045fa2525d518f3143650c7a2bfe7a`.
It records all five registered commands passing: the full suite reported
`4249 passed, 11 skipped`, the focused governance suite reported `1251
passed, 2 skipped`, and the Runtime asset, template mirror, and host-lock
checks passed.

## Immutability and release boundary

These three earlier TASK-AR-654 Compound records remain byte-for-byte
immutable and are not renamed, edited, or deleted:

- `agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json`;
- `agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json`;
- `agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json`.

This amendment authorizes only the new append-only record, its deterministic
index projection, and lifecycle/evidence references. Native Windows
3.10/3.11/3.12 evidence remains unavailable locally, so the unit remains
`verification_status: failed` and the maximum eventual local verdict is
`PASS_PENDING_NATIVE_WINDOWS_CI`. Claim release, integration, Scribe
disposition, consumer pilot mutation, versioning, CI dispatch, publication,
deployment, push, and external release remain unauthorized. Fresh exact-
commit W4a, independent W4b, and skeptic review are still required.
