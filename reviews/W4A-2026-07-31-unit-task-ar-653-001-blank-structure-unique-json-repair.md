---
title: TASK-AR-653 Scribe Blank Structure and Unique JSON Repair W4a
date: 2026-07-31
created_at: 2026-07-31T02:59:56+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: f285aa0a11a1b0456be90001706de158b2fde8db
repair_parent: f285aa0a11a1b0456be90001706de158b2fde8db
reviewed_commit: 26e50b9781ba8ca4efc785c5c899dcc834e471da
reviewed_tree: d7097cc34ff02b7f07f07a2ed663872be7b9ee75
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..26e50b9781ba8ca4efc785c5c899dcc834e471da
repair_range: f285aa0a11a1b0456be90001706de158b2fde8db..26e50b9781ba8ca4efc785c5c899dcc834e471da
worker_identity: le-20260730-234934-kst-ar653004
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-semantic-delta-identity-final.md
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731025837.json
claim_disposition: remain_claimed_pending_fresh_independent_w4b
tags: [w4a, scribe, markdown, blank-lines, json, duplicate-members, replay, repair, regression]
---

# TASK-AR-653 Scribe Blank Structure and Unique JSON Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`26e50b9781ba8ca4efc785c5c899dcc834e471da` repairs both P1 findings from
the latest independent review:

1. Markdown cleanup validation now preserves every source row, including blank
   rows, so a blank insertion or deletion cannot change protected block
   structure while disappearing from the matcher; and
2. state-source JSON is decoded with recursive duplicate-member rejection in
   both projection parsing and cleanup-delta validation.

This is worker self-review and machine evidence, not independent acceptance.
Claim `CLAIM-20260730-234934-task-ar-653-ar653004` remains claimed. Claim
release, merge-queue admission, W5, versioning, publication, deployment, and
consumer mutation remain prohibited until a fresh independent W4b approves
the exact commit and tree above.

## Blocking Evidence Preserved

The immutable blocking report is:

`reviews/W4B-2026-07-31-unit-task-ar-653-001-semantic-delta-identity-final.md`

Its SHA-256 is:

`3274154e63152816467c1d81a3afa990be07e964235ac0e49baa07e9d61ab7e1`

The report and generated index were committed separately as
`f285aa0a11a1b0456be90001706de158b2fde8db` before implementation changed.
No earlier W4b evidence was edited or replaced.

## RED Before Repair

The new public-API regression matrix was first run against the blocking
implementation:

```text
18 failed, 103 deselected in 4.06s
```

All 18 expected negatives failed open:

- six Markdown blank-line boundary changes at record time;
- the same six boundary changes after cleanup-receipt rebinding and replay;
- duplicate JSON outer collection, entry field, and summary field at record
  time; and
- the same three duplicate-member families after receipt rebinding and replay.

The Markdown matrix includes Setext headings, raw HTML blocks, list
continuations, fenced blocks, comments, and ATX-heading boundaries. The JSON
matrix includes an arbitrary duplicate collection, a hidden duplicate entry
identity, and a non-exact duplicate `candidate_count` in the bounded summary.

## Repair Invariants

### Markdown source positions include blank rows

The delta matcher now receives the complete `splitlines()` sequence for both
the committed baseline and live after-source. Cleanup-plan `source_order`
values already refer to physical source rows, so no logical-index remapping is
needed.

- Protected non-candidate rows, including blank rows, must remain exact and in
  their original order.
- Only a bound candidate row may be deleted or replaced by the exact bounded
  summary form.
- A blank row cannot be inserted or removed beside a Setext underline, HTML
  block, list continuation, fence, comment, or heading.
- Existing continuation ownership and structurally empty heading checks remain
  in force.

The same `_validate_cleanup_delta()` path is used while recording a cleanup
and while replaying its receipt.

### Every state JSON object has unique members

`parse_json()` and `_json_cleanup_view()` now share a recursive
`object_pairs_hook`. Any repeated member name raises before last-value
collapse can hide raw canonical content.

- Duplicate outer collection names are rejected.
- Duplicate names inside collection entries are rejected.
- Duplicate names inside cleanup-summary objects are rejected.
- Unique-member objects remain semantic rather than byte-order bound:
  whitespace and object-key reordering are accepted.
- Collection identity, collection entry order, outer values, candidate
  positions, summary count, and summary plan digest remain bound as before.

## Regression and Compatibility Evidence

The focused repair matrix, including the positive unique-key reorder case:

```text
19 passed, 103 deselected in 3.19s
```

The full Scribe module suite before the added positive case:

```text
121 passed in 10.77s
```

The final registered unit verification:

```text
196 passed in 47.98s
template-mirror: expected=84 common=84 identical=81 intentional=3 findings=0
```

Official evidence:

- path:
  `reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731025837.json`
- SHA-256:
  `2a3a73e094344c4a5ad7c9bcf9207ad7b18b69bb94f487deb5bd837b67775d5d`

## Full and Supplemental Verification

Exact candidate full suite:

```text
3084 passed, 3 skipped, 4 warnings in 174.16s
```

The four warnings are the existing UI-console invalid-escape
`DeprecationWarning` family and are unrelated to this repair.

| Check | Result |
| --- | --- |
| Three-way portable state module byte parity | pass |
| Python compile for all three portable modules | pass |
| `git diff --check` | pass |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Host lock freshness | pass |
| Wheel dotfile packaging | 2 passed |

## Live Read-only Scribe Observation

No canonical source was written. A read-only evaluation reported:

```text
hot_count=773
source_debt=overdue
active_work.task_ids=["TASK-AR-648","TASK-AR-653"]
active_work.claim_count=3
active_coverage=incomplete
cleanup_outcome=none
readiness=blocked
closure_blocking=true
```

The runtime therefore remains fail-closed while source debt and active-work
coverage are unresolved.

## Footprint and Boundary

Repair range
`f285aa0a11a1b0456be90001706de158b2fde8db..26e50b9781ba8ca4efc785c5c899dcc834e471da`
changes exactly five declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `tests/test_scribe_due.py`
- `tests/fixtures/host/agent_runtime.lock.json`

No credentials, provider calls, live network, broker/order action, database
migration, notification, consumer-repository write, version bump, tag, push,
package publication, deployment, release, merge, claim release, or W5 action
occurred.

## Fresh W4b Request

A distinct verifier must review both:

- complete implementation range:
  `ae998f7b3b96def7347be7317e3cadda6078150f..26e50b9781ba8ca4efc785c5c899dcc834e471da`
- latest repair range:
  `f285aa0a11a1b0456be90001706de158b2fde8db..26e50b9781ba8ca4efc785c5c899dcc834e471da`

The verifier should independently probe:

1. blank insertion and deletion at Setext, raw-HTML, list, fence, comment, and
   heading boundaries during record and replay;
2. duplicate JSON members at every object depth during planning, record, and
   replay;
3. valid unique-key reordering, whitespace, deletion, and exact summary paths;
4. the prior semantic-delta, exact-identity, exact no-touch, and Git audit-view
   attack families; and
5. matcher resource bounds, three-way parity, host lock, package, and declared
   footprint.

Only a fresh `APPROVE` with P0=0 and P1=0 may permit claim release and W5.
