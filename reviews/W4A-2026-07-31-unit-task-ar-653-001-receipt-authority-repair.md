---
title: TASK-AR-653 Scribe Receipt and Authority Repair W4a
date: 2026-07-31
created_at: 2026-07-31T00:37:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
reviewer: le-20260730-234934-kst-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
rejected_candidate: a0bf5f636063f11d90b1c0d33275c7287e1831b0
repair_parent: b43c6957f00dbe4ab2d29159dfc615a675464756
candidate_commit: 4907227f566a27794e945ee646394124c473599f
candidate_tree: 92b2654aed2db50e07fe7ac4b1c9c66d63671bba
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731003459.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-653-001.md
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001.md
tags: [w4a, scribe, source-debt, cleanup-receipt, authority, repair, regression]
---

# TASK-AR-653 Scribe Receipt and Authority Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `4907227f566a27794e945ee646394124c473599f` repairs both P1
fail-open paths reported by the independent review of candidate
`a0bf5f636063f11d90b1c0d33275c7287e1831b0`:

1. a forged top-level baseline count can no longer manufacture a cleanup
   reduction; and
2. path or filename shape can no longer stand in for Scribe cleanup authority
   or an owner no-touch decision.

This is worker self-review, not acceptance. The original W4a and the
independent `REVISE` report remain immutable historical evidence. The claim
must remain claimed until a distinct verifier reviews this exact repaired
candidate and returns a fresh W4b approval with no P0/P1 findings.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Reviewed base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Rejected implementation | `a0bf5f636063f11d90b1c0d33275c7287e1831b0` |
| Repair parent containing REVISE evidence | `b43c6957f00dbe4ab2d29159dfc615a675464756` |
| Repaired implementation | `4907227f566a27794e945ee646394124c473599f` |
| Repaired tree | `92b2654aed2db50e07fe7ac4b1c9c66d63671bba` |
| Worker | `le-20260730-234934-kst-ar653004` |
| Claim | `CLAIM-20260730-234934-task-ar-653-ar653004` |
| Declared footprint | 17 paths |
| Changed implementation footprint | 14 paths |
| Undeclared changed implementation paths | 0 |

The claim remains canonically `claimed`, although its original fixed lease
expired at `2026-07-31T00:19:34+09:00`. The absence of an in-flight heartbeat
command is already assigned to TASK-AR-655. This report does not hand-edit or
reinterpret claim lifecycle state.

## RED: Independent Failures Reproduced

The repair began by adding public-flow regression tests for the two W4b
findings. Before the implementation change, the focused Scribe slice produced:

```text
6 failed, 29 passed
```

The six failures covered:

- forged top-level `hot_count`;
- altered before-source digest;
- fabricated cleanup-plan digest;
- receipt replay after each of those three mutations, including recomputed
  receipt self-digests;
- an unrelated task-shaped authorization;
- an unrelated `REVIEW-*` file used as an owner no-touch decision; and
- missing or duplicate authority fields.

The intentionally overlapping cases prove both record-time rejection and
read-time replay rejection; a caller cannot bypass the repair by fabricating a
self-consistent receipt envelope.

## GREEN: Baseline and Plan Are Recomputed

The cleanup baseline is now validated as structured evidence rather than
trusted caller data:

- every source binding is schema-checked and repository-contained;
- source identity, presence, SHA-256 digest, and hot count are recomputed;
- the top-level hot count must equal the sum of per-source counts;
- the declared source count must match the complete binding set;
- the complete cleanup-plan schema, candidates, counts, active-work digest,
  source fingerprints, and canonical plan digest are recomputed; and
- `before_source_binding_digest` binds the receipt to that exact baseline.

The receipt embeds `before_sources` and the complete
`before_cleanup_plan`. `_cleanup_outcome()` repeats the same validation during
replay. Recomputing only the outer `receipt_digest` after tampering is
therefore insufficient.

## GREEN: Authority Is Explicit and Digest-Bound

Cleanup authorization must now be an active canonical TASK or UNIT-TASK record
whose path and frontmatter agree. It must declare:

```yaml
schema_version: agent-runtime-work-item/v1
work_id: <matching active TASK or UNIT-TASK ID>
kind: task # or unit
status: in_progress
scribe_authorization: cleanup
scribe_authorized_by: <non-empty identity>
scribe_authorized_role: lead-engineer # or doc-steward / owner
scribe_source_binding_digest: <exact baseline source-binding digest>
scribe_cleanup_plan_digest: <exact cleanup-plan digest>
```

Duplicate authority fields are rejected. Merely creating a Markdown file with
a `TASK-*` filename is not authority.

No-reduction cleanup additionally requires exact JSON under
`reviews/DECISION-*.json` or `reviews/OWNER-DECISION-*.json`, using schema
`agent-runtime-scribe-owner-decision/v1`. The record must explicitly say
`decision: no_touch`, bind the work ID, authorization reference, source
binding, and cleanup plan, identify an owner approver and role, and contain a
timezone-aware decision timestamp. Duplicate JSON members are rejected.
Unrelated reviews and audit prose cannot unblock closure.

The Scribe skill and CLI help expose this same contract. Evaluation remains
read-only by default; this work neither edits canonical Scribe sources nor
creates cleanup authority on the owner's behalf.

## Positive and Negative Proof

Regression coverage confirms:

- unchanged sources with a forged scalar remain blocked;
- source- or plan-binding mutations fail both recording and replay;
- unbound or duplicated authorization records fail closed;
- unrelated reviews and malformed/duplicated decision JSON fail closed;
- a legitimate, bound reduction still becomes `verified_reduction`;
- a legitimate, exact owner no-touch decision still becomes
  `owner_decision`; and
- active coverage must be complete and current before any receipt can be
  recorded.

The live checkout read-only result remains:

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

No projection or cleanup receipt was written during this live check.

## Portable and Host Integrity

- Canonical, repository-script, and packaged-template
  `state_projection.py` copies are byte-identical.
- The Scribe CLI source/template pair is byte-identical.
- The template mirror gate reports `expected=84`, `common=84`,
  `identical=81`, `intentional=3`, `findings=0`.
- The regenerated host lock is current.
- Runtime asset usage reports 38 assets, 479 uses, 0 block findings, and
  0 watch findings.
- `git diff --check` passes over the complete implementation range.

## Verification

| Verification | Result |
| --- | --- |
| Repair RED slice before implementation | `6 failed, 29 passed` |
| Registered focused suite after repair | `116 passed` in `39.34s` |
| Final full Runtime suite | `3004 passed, 3 skipped, 4 known UI warnings` in `161.30s` |
| Model-routing regression | `20 passed` |
| Lock and lock-regeneration regression | `23 passed` |
| Host lock current check | pass |
| Three-way state-projection byte comparison | pass |
| Scribe CLI source/template byte comparison | pass |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Runtime asset usage gate | 38 assets, 479 uses, 0 block, 0 watch |
| Claim footprint | 17 declared, 14 changed implementation paths, 0 undeclared |

The four full-suite warnings are the existing UI beta route-sweep invalid
escape deprecation warnings. No test failed.

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731003459.json`
(SHA-256
`45ff60458f0b0cb89778b901f89de8dd4908d2f789de819713d3b450ef062fa9`)
binds the repaired candidate's registered 116-test suite and mirror gate.
The older `20260731000019` and `20260730235407` files are retained only as
evidence for superseded candidates and must not be used for repaired
acceptance.

## Boundary and Next Gate

No consumer primary was modified or executed beyond observation. No
credential, provider, live network, broker, order, database migration,
notification, version, tag, package, push, publication, deployment, or release
action occurred.

Request a fresh independent implementation W4b over repaired implementation
`4907227f566a27794e945ee646394124c473599f` and this W4a commit. Only a
distinct verifier's `APPROVE` with P0/P1 both zero permits claim release and
local W5 integration.
