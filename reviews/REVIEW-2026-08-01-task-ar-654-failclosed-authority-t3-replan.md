---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-01T00:45:10+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
tags: [task-ar-654, t3, compound, fail-closed, utf8, claim-authority, bounded-read]
---

# TASK-AR-654 fail-closed authority T3 replan

## Why replan

The physical-line candidate
`0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458` (tree
`5b2d194c38ffbc77fde12432ae32c6bfab0a7e86`) correctly rejects all Python
`splitlines()` separators. Fresh independent W4b and skeptic reviews still
returned `REVISE` because the actual closure endpoints expose two additional
fail-closed defects and the current lifecycle evidence cannot close cleanly.

The exact blocking reports are:

- `reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md`;
- `reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md`.

The prior W4a remains append-only evidence of what passed, but its zero-finding
verdict is superseded for release purposes.

## Stable defect identities and prior-knowledge search

Exact signature and phrase searches returned no prior canonical record for:

- `defect:accepted-watch-malformed-utf8-fail-open:eac1aefa14add5d1`;
- `defect:claim-repeated-failure-signals-lost-at-closure:1da2d2d41b194afb`;
- `defect:accepted-watch-unbounded-raw-file-read:ceb1edfdb452964a`.

The existing physical-line record remains prior/current-work knowledge for
`defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694`.
New records will be created only after their durable prevention tests and fresh
verification evidence exist.

## Confirmed defects

1. Strict UTF-8 decode errors escape the accepted-watch boundary. `work close`
   produces a traceback and the best-effort Stop wrapper silently approves.
2. Active-claim `repeated_failure` and `defect_signatures` are used to locate a
   unit but discarded before closure evaluation. A generic review or low churn
   can therefore bypass a claim-declared Compound obligation.
3. Accepted-watch Markdown and JSON are read without a raw-size bound, so an
   authority file can consume unbounded resources before validation.
4. The current Compound directly links the unit but not its parent task.
5. Two Markdown reviews were incorrectly placed in JSON-only `evidence_refs`.

## Repair decision

1. Add failure-first regressions for malformed UTF-8 Markdown and JSON through
   the source and packaged helpers, `work close`, direct closure evaluation,
   and the actual Stop wrapper. Decode failures must become bounded
   invalid-watch findings, never exceptions.
2. Add one shared accepted-watch raw-byte ceiling. Read at most `limit + 1`,
   reject oversized Markdown and JSON through the same bounded finding, and
   retain exact-boundary positive controls.
3. Merge only identity-matched active-claim repeat fields into closure
   contexts. Preserve deterministic order, ignore released/expired or
   unrelated claims, and keep ambiguous active claims fail-closed without
   leaking one claim's authority into another.
4. Persist the same repeated-failure identities on TASK-AR-654 and its unit so
   explicit work-id assessment is truthful; this state repair does not replace
   the claim-to-Stop product regression.
5. Make the still-unmerged current-work Compound directly usable by both task
   and unit under the repository's append-only/identity rules, regenerate the
   index, and create canonical records for the newly verified defect families.
6. Keep only machine JSON receipts in `evidence_refs`; put W4a, W4b, and
   skeptic Markdown in `review_refs`.
7. Replay unit and task closeout validation, the physical-line and new
   failure-first matrices, the registered focus suite, the full suite, store,
   mirror, host lock, security, and footprint checks on one exact candidate.
8. Require a new W4a, a distinct independent W4b, and a fresh skeptic approval
   after every implementation and lifecycle repair above is committed.

## Scope and safety boundary

The existing unit footprint already owns the accepted-watch helpers,
`closure_gate.py`, both registered consumer test files, the current Compound
record/index, mirror contract, and host lock. No consumer repository is added.

Do not rewrite or delete legacy Compound history. Do not release the active
claim on either `REVISE` report. No credential, provider, live network,
package installation, database, broker, order, notification, consumer write,
version, tag, publication, push, deploy, or release action is authorized.
