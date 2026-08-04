---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-precommit-authority-seams
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-precommit-audit
reviewer: codex-task-ar-654-precommit-diff-reviewer
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 4, P2: 4}
baseline_commit: dcf75a387a3e6c9379e6165f0eff9646d71bad1e
baseline_tree: db566839e352541861c1eb7f6c2a7beff279d25d
candidate_kind: uncommitted-working-tree
release_authorized: false
created_at: 2026-08-02T18:25:27+09:00
tags: [task-ar-654, precommit, claim-reader, publication, rollback, compound-coverage, strict-json, sync]
---

# TASK-AR-654 precommit authority-seam audit

## Verdict

`REVISE — P0: 0, P1: 4, P2: 4.`

The claim-transaction implementation passed its initial full Runtime suite,
but independent dirty-tree review reproduced authority gaps at the seams
between publication, rollback, canonical reading, witness validation, and
Compound coverage. This is not an exact-commit W4 review. Baseline `dcf75a38`
contains the accepted transaction replan only; all reviewed implementation
bytes remain an uncommitted candidate and provide no release authority.

## P1 findings

1. POSIX exclusive publication committed the destination before removing its
   sidecar. If sidecar cleanup raised, the caller received failure while the
   destination remained, so higher-level rollback never captured the new
   authority object.
2. Role-overlay rollback unlinked by path without proving that the object was
   still the one created by that call. Replacing a first artifact before a
   later failure caused the competitor replacement to be deleted.
3. Active and linked-released closeout readers bypassed the shared canonical
   claim reader. A matching `CLAIM-bad!.json` could contribute authority, and
   store initialization accepted a witness whose unknown status the canonical
   reader rejected.
4. Closure treated any valid current-work Compound as sufficient. A work item
   with two declared defect signatures could close when the linked record
   covered only one, leaving the other repeated failure un-compounded.

## P2 findings

1. Shared JSON decoding accepted non-finite constants and duplicate object
   keys.
2. Existing role overlay idempotency checked handoff/log object type but not
   the deterministic seed content, so corrupted regular artifacts were reused.
3. Atomic alias tests lacked an actual native Windows junction parent for all
   four write/publish APIs.
4. Sync could commit claim-store migration and one or more template writes,
   then report `claim-store migration failed` and `applied=0` after a later
   write error.

## Stable signatures and exact prior-knowledge search

Canonical `compound_record search --no-legacy --json` returned `[]` for all
six additional signatures:

- `defect:atomic-publisher-reports-failure-after-committed:2e080352410acda0`;
- `defect:role-overlay-rollback-deletes-replacement-artifa:24910ed49f07f9b7`;
- `defect:claim-store-witness-accepts-unknown-claim-status:8e42ea5ea2d844c9`;
- `defect:partial-compound-coverage-satisfies-declared-def:90587dadec03fe8f`;
- `defect:claim-json-accepts-nonfinite-or-duplicate-fields:2fc824544a55622d`;
- `defect:sync-reports-zero-after-committed-claim-migratio:4317243460108472`.

The corrupted-overlay and native-junction cases refine the already registered
incomplete-overlay and aliased-parent signatures. No prior Compound is edited,
and no new record is created before prevention and fresh Verify evidence.

## Required disposition

Add RED regressions for every seam, repair the shared source/template assets,
and prove exact publication truth, identity-bound rollback, canonical reader
reuse, known witness lifecycle, complete declared-signature coverage, strict
JSON, deterministic overlay prefixes with supported append behavior, native
Windows junction selection, and truthful sync partial-state reporting. Then
rerun all affected suites and the full Runtime suite before creating one
append-only Compound that covers every still-uncovered signature.

## Safety boundary

Do not release the claim, run external CI, mutate consumer repositories, bump
the version, tag, publish, push, deploy, or perform any other external release
action from this audit.
