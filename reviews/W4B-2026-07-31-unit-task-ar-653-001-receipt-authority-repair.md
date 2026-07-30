---
title: TASK-AR-653 Scribe Receipt and Authority Repair Independent W4b
date: 2026-07-31
created_at: 2026-07-31T00:48:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
reviewed_base_tree: ddfb67269b99706596638db147f8178c9fd39198
rejected_candidate: a0bf5f636063f11d90b1c0d33275c7287e1831b0
rejected_candidate_tree: ec047946878fcc3d22479ff91efcb348378ffc5d
repair_implementation_commit: 4907227f566a27794e945ee646394124c473599f
repair_implementation_tree: 92b2654aed2db50e07fe7ac4b1c9c66d63671bba
reviewed_commit: 679b1554ebb79e3119227a5eb0f9417d1c59116b
reviewed_tree: 4a749d8351e6f81326d89288d7b99eb6dc9c9fd6
full_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..679b1554ebb79e3119227a5eb0f9417d1c59116b
implementation_range: ae998f7b3b96def7347be7317e3cadda6078150f..4907227f566a27794e945ee646394124c473599f
repair_range: a0bf5f636063f11d90b1c0d33275c7287e1831b0..4907227f566a27794e945ee646394124c473599f
verifier_agent_instance_id: qa-20260731-ar653-receipt-authority-repair-w4b
verified_by: qa-20260731-ar653-receipt-authority-repair-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_receipt_authority_repair_w4b
worker_identity: le-20260730-234934-kst-ar653004
prior_verifier_identity: qa-20260731-ar653-final-implementation-w4b
independence_status: independent
implementation_reviewed: true
w4b_acceptance: false
pre_report_worktree_status: clean
post_report_worktree_status: report_only_untracked
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
w4a_evidence: reviews/W4A-2026-07-31-unit-task-ar-653-001-receipt-authority-repair.md
work_verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731003459.json
prior_revise_evidence: reviews/W4B-2026-07-31-unit-task-ar-653-001.md
full_suite_basis: exact_parent_w4a_assertion_not_independently_rerun
tags: [w4b, scribe, cleanup-receipt, authority, trust-anchor, independent-verification, revise]
---

# TASK-AR-653 Receipt and Authority Repair Independent W4b

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 0`

The repair closes the narrow reproductions from the prior W4b: a lone forged
top-level count, a lone source or plan digest mutation, a task-shaped empty
file, an unrelated `REVIEW-*` file, and duplicate declared authority fields
all fail closed. The registered positive reduction and exact owner no-touch
paths also pass.

The underlying trust boundary is not closed, however. Two stronger
independent adversarial checks still turn an overdue or unchanged source into
a closure-ready result:

1. all nested baseline or receipt bindings can be recomputed and the mutable
   authorization can be rebound, after which a false reduction is accepted;
   and
2. malformed authority identities are coerced to strings, while conflicting
   task identities are not rejected, so non-canonical records can authorize a
   reduction or owner no-touch outcome.

Both paths produce `closure_blocking=false` or `readiness=ready` without the
required replayable cleanup or valid owner identity. This exact candidate
must not release its claim or enter W5. A repaired candidate needs another
fresh W4a and independent W4b.

Verifier `qa-20260731-ar653-receipt-authority-repair-w4b` is distinct from
worker `le-20260730-234934-kst-ar653004` and prior verifier
`qa-20260731-ar653-final-implementation-w4b`.

## Exact reviewed state

| Identity | Exact value |
| --- | --- |
| Review base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Base tree | `ddfb67269b99706596638db147f8178c9fd39198` |
| Rejected implementation | `a0bf5f636063f11d90b1c0d33275c7287e1831b0` |
| Rejected tree | `ec047946878fcc3d22479ff91efcb348378ffc5d` |
| Repair implementation | `4907227f566a27794e945ee646394124c473599f` |
| Repair tree | `92b2654aed2db50e07fe7ac4b1c9c66d63671bba` |
| W4a/evidence HEAD | `679b1554ebb79e3119227a5eb0f9417d1c59116b` |
| W4a/evidence tree | `4a749d8351e6f81326d89288d7b99eb6dc9c9fd6` |
| W4a HEAD parent | `4907227f566a27794e945ee646394124c473599f` |

The worktree and index were clean before this report. The delta from repair
implementation to W4a HEAD contains only the unit, review index, fresh machine
evidence, and W4a report. No implementation changes are hidden after the
candidate.

The claim declares 17 target paths. Fourteen declared implementation paths
changed, zero changed implementation paths are undeclared, and the three
declared-but-unchanged paths are:

- `scripts/session_start_hook.py`
- `src/agent_runtime/doctor.py`
- `src/agent_runtime/templates/project/scripts/session_start_hook.py`

`git diff --check` passes over the complete review range.

## P1-1 — Self-consistent rebinding is mistaken for a trust anchor

The repair validates the shape and internal arithmetic of caller-controlled
baseline data, but does not anchor it to immutable pre-cleanup evidence.

- `_validated_receipt_sources()` validates that a digest looks like SHA-256
  and that `hot_count` is a non-negative integer
  (`src/agent_runtime/state_projection.py:1071-1135`). It does not establish
  that the stored digest and stored count came from the same source content.
- `_validated_projection_baseline()` sums those caller-supplied counts and
  compares other caller-supplied aggregate fields
  (`src/agent_runtime/state_projection.py:1267-1307`).
- The source-binding and plan digests are ordinary canonical checksums over
  mutable payloads (`src/agent_runtime/state_projection.py:1138-1139`,
  `1261-1263`), not independent or append-only attestations.
- `record_cleanup()` obtains projection status but discards it, then trusts the
  internally consistent baseline and the live mutable task authorization
  (`src/agent_runtime/state_projection.py:2077-2093`, `2124-2129`).
- Receipt replay repeats the same internal checks and consults that same
  mutable authorization (`src/agent_runtime/state_projection.py:1550-1627`).

### Independent public-flow reproduction A: no source edit

An isolated repository was created with one source containing exactly 11 hot
items and an active Scribe task present before projection generation. The
generated projection was changed coherently:

- per-source `hot_count`: `11 -> 16`;
- top-level and source-debt counts: `11 -> 16`;
- the source-binding digest was recomputed; and
- the active Scribe authorization was rebound to that recomputed digest.

The source body and its SHA-256 digest never changed. `record_cleanup()` still
returned:

```text
source_was_edited=false
before_hot_count=16
resulting_hot_count=11
cleanup_outcome.status=verified_reduction
readiness=ready
```

This is the original forged-reduction failure in a fully internally
consistent form. The registered test changes one field at a time and therefore
does not cover it.

### Independent public-flow reproduction B: replay after full rebinding

A legitimate `16 -> 11` receipt was first recorded. Its historical
`before_sources[0].hot_count` and `before_hot_count` were then changed to 99.
The verifier recomputed:

- `before_source_binding_digest`;
- the live task authorization binding; and
- the outer `receipt_digest`.

Read-only `evaluate_state()` returned:

```text
actual_original_before_hot=16
forged_before_hot=99
cleanup_outcome.status=verified_reduction
cleanup_outcome.valid=true
readiness=ready
```

Recomputing the outer digest was explicitly included. Rebinding the nested
digest and mutable authority demonstrates that replay checks consistency, not
historical authenticity.

### Required repair

- Anchor the exact generated baseline to evidence that cannot be rewritten
  together with the receipt. Suitable designs include an append-only
  generation event, a pre-cleanup Git blob/commit identity, or an equivalent
  immutable audit record referenced by both authorization and receipt.
- When the projection is still fresh, independently reparse the matching
  current source and reject any stored count that disagrees with the content
  behind its digest.
- For a legitimately stale post-cleanup projection, replay the immutable
  pre-cleanup anchor rather than accepting a newly rebound live task record.
- Bind the receipt to the exact authorization artifact identity/content
  version, not only to fields in a mutable path.
- Add negative tests that recompute every nested binding plus the outer receipt
  digest, including a no-source-edit case and a post-receipt authority rewrite.

## P1-2 — Malformed identities still authorize closure

The owner decision schema checks its field set, role, digests, and timestamp,
but `_authority_identity()` first converts any truthy object with `str()`
(`src/agent_runtime/state_projection.py:1353-1360`). As a result, a JSON object
is accepted as `approved_by`. An exact-schema `DECISION-*.json` containing:

```json
"approved_by": {"name": "not-a-scalar"}
```

was accepted by `_validate_owner_decision()` and produced:

```text
cleanup_outcome.status=owner_decision
readiness=ready_with_owner_decision
closure_blocking=false
```

The task frontmatter parser has the complementary problem. It lexically
extracts strings rather than applying typed YAML scalar rules
(`src/agent_runtime/state_projection.py:1363-1391`), so
`scribe_authorized_by: null` becomes the non-empty string `"null"`.
Furthermore, `_validate_task_authorization()` prefers `work_id` and never
rejects a conflicting `id` (`src/agent_runtime/state_projection.py:1435-1454`).

An active record present before projection with:

```yaml
id: TASK-UNRELATED
work_id: TASK-SCRIBE
scribe_authorized_by: null
```

plus otherwise matching bindings was accepted from path `TASK-SCRIBE.md`.
After a source reduction, it produced `verified_reduction` and
`readiness=ready`. The projection itself had tracked `TASK-UNRELATED`, proving
that active coverage did not normalize the conflicting identities away.

The repair does correctly reject duplicate recognized frontmatter keys,
duplicate JSON members, filename-only task records, unrelated reviews, wrong
roles, and mismatched standalone digests. Those protections do not validate
the approver's type or the record's single canonical identity.

### Required repair

- Require authority identities to be actual strings before trimming or
  redaction; reject JSON containers, numbers, booleans, and null.
- Parse task frontmatter with a bounded, duplicate-aware typed YAML subset, or
  enforce an equivalently strict scalar grammar. Reject YAML null/boolean/
  collection values and placeholder identities.
- Require every present identity field to agree:
  `id == work_id == path stem`. For units, also require the unit/task parent
  relationship to match its canonical directory and frontmatter.
- Add malformed-type matrices for `scribe_authorized_by` and `approved_by`,
  plus conflicting `id`/`work_id`/path and unit-parent cases.

## Verification ledger

| Independent check | Result |
| --- | --- |
| Registered focused suite | `116 passed` in `38.44s` |
| Named baseline/receipt/authority/no-touch positive and negative slice | `14 passed, 28 deselected` |
| Fully rebound independent adversarial flows | **4 fail-open reproductions** |
| Model-routing regression | `20 passed` |
| Lock and lock-regeneration regression | `23 passed` |
| Template mirror gate | expected/common 84, identical 81, intentional 3, findings 0 |
| Host lock current check | pass |
| Three-way state-projection byte comparison | pass |
| Scribe CLI source/template byte comparison | pass |
| Runtime asset usage gate | 38 assets, 479 uses, 0 block, 0 watch |
| Footprint | 17 declared, 14 changed implementation paths, 0 undeclared |
| Full-range `git diff --check` | pass |

The canonical, repository-script, and packaged-template
`state_projection.py` files share SHA-256
`977b24b196d53d1446397e7cdacdd5f60454213c631f3f09340b35f7f67a1d58`.
The Scribe CLI source/template pair shares SHA-256
`c3e3c6cb5157671d6a5032697a404d45ff5a9723cb0047ed9e52ca2439173ca3`.
The two P1 findings therefore affect the portable and generated-host copies,
not only one mirror.

The live checkout read-only check remained blocked and did not modify its
projection (before/after SHA-256
`7ba19af01a429e7f1c818e9b835ef9a3856f87c1bd1457fbe06bd9653f90bf68`):

```text
hot_count=773
overdue_sources=["STATUS.md"]
projection.status=fresh
active_work.task_ids=["TASK-AR-648","TASK-AR-653"]
active_work.claim_count=3
active_coverage.status=incomplete
cleanup_plan.status=available
cleanup_plan.candidate_count=10
cleanup_outcome.status=none
closure_reasons=["source-debt-overdue","active-coverage-incomplete"]
readiness=blocked
closure_blocking=true
```

## Evidence binding and full-suite basis

Machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731003459.json`
has SHA-256
`45ff60458f0b0cb89778b901f89de8dd4908d2f789de819713d3b450ef062fa9`.
It records the worker's 116-test focused suite and mirror gate.

The repair W4a has SHA-256
`f455ef4eb6b1f4f6d9462547814edcefa925dd52256d64184bb41d70eaee9969`
and is committed in the direct child of the exact implementation candidate.
It asserts `3004 passed, 3 skipped, 4 known UI warnings in 161.30s` for the
full Runtime suite. This independent review relies on that exact-parent
full-suite assertion and did not rerun the full suite. The registered suite,
cross-cutting gates, and focused adversarial checks were rerun independently.
The deterministic P1 public-flow reproductions cannot be overturned by an
additional broad-suite pass.

## Boundary and disposition

The claim must remain claimed pending another repair and fresh independent
W4b. No implementation file, task/unit record, claim, index, lifecycle
record, canonical Scribe source, or generated projection was modified. No
claim release, commit, merge, cleanup, push, publish, deployment, version, tag,
package, credential, provider, or external action occurred.

This report is the only repository write made by this verifier. After report
creation, the expected worktree status is exactly this one untracked report.
