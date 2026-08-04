---
title: TASK-AR-653 Scribe Semantic Delta and Exact Identity Repair W4a
date: 2026-07-31
created_at: 2026-07-31T02:33:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: 059bc5fb87109eb5095960b28c30a8431e71c821
repair_parent: 059bc5fb87109eb5095960b28c30a8431e71c821
reviewed_commit: 30fdf025ee3d15f88678934c827a287916f64e04
reviewed_tree: c868d2fea06e952b699bce6223885b04a22137d2
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..30fdf025ee3d15f88678934c827a287916f64e04
repair_range: 059bc5fb87109eb5095960b28c30a8431e71c821..30fdf025ee3d15f88678934c827a287916f64e04
worker_identity: le-20260730-234934-kst-ar653004
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-audit-view-plan-delta-repair.md
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731023129.json
claim_disposition: remain_claimed_pending_fresh_independent_w4b
tags: [w4a, scribe, semantic-delta, exact-identity, cleanup-summary, replay, repair, regression]
---

# TASK-AR-653 Scribe Semantic Delta and Exact Identity Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`30fdf025ee3d15f88678934c827a287916f64e04` repairs both P1 findings in
the blocking independent report:

1. cleanup validation now recognizes only a position-bound rewrite language,
   rather than accepting any after-source that contains protected raw lines as
   an ordered subsequence; and
2. TASK, UNIT, and owner identities must satisfy the ASCII token grammar as
   their exact logical values, without trimming whitespace or controls into a
   valid principal.

This is worker self-review and test evidence, not independent acceptance.
Claim `CLAIM-20260730-234934-task-ar-653-ar653004` remains claimed. Release,
merge queue admission, W5, versioning, publication, deployment, and consumer
mutation remain prohibited until a fresh independent W4b approves the exact
commit and tree above.

## Blocking Evidence Preserved

The immutable blocking report is:

`reviews/W4B-2026-07-31-unit-task-ar-653-001-audit-view-plan-delta-repair.md`

Its SHA-256 is:

`6ac964ab539bb57c913bf2ccbfdbe3d8919607602d49a479a015a6e5701a2525`

The report was indexed and committed separately as
`059bc5fb87109eb5095960b28c30a8431e71c821` before implementation changed.
The report found:

- inserted Markdown structure could hide a protected row while retaining its
  raw line; and
- padded or control-suffixed authorization identities were accepted after
  normalization.

No prior W4b evidence was edited or replaced.

## RED Before Repair

New regressions were first executed against the prior implementation:

```text
12 failed, 20 passed, 59 deselected in 3.72s
```

The failures independently covered:

- HTML-comment and fenced-code wrapping of a protected Markdown row;
- inserted headings and list structure outside candidate positions;
- arbitrary JSON insertion outside the candidate span;
- candidate movement across a protected Markdown row;
- padded ASCII and NBSP TASK/UNIT identities; and
- padded, newline-suffixed, and NBSP owner identities.

Positive bounded Markdown and JSON cleanup paths remained green in the same
RED run. The failures therefore isolated the two W4b bypasses rather than
breaking all cleanup behavior.

## Repair Invariants

### Position-bound cleanup rewrite language

For each changed source the validator reconstructs the committed baseline and
maps cleanup-plan `source_order` values to exact logical rows.

- Every protected Markdown nonblank row and every protected JSON entry must be
  emitted exactly, in its original order and position relative to candidate
  spans.
- A bound candidate may remain unchanged or be deleted.
- Candidate output may not contain an arbitrary inserted row or entry.
- Markdown blank-line formatting remains outside the semantic row model.
- JSON collection identity and all outer object structure remain exact.
- The matcher is a bounded state traversal. Only the at-most-ten plan
  candidates add alternate states, so validation does not use an unbounded
  quadratic diff over the source.

The same function is called during receipt creation and receipt replay.
Rebinding top-level source digests and recomputing the unkeyed receipt digest
therefore does not bypass the plan delta.

### Bounded summary forms

A replacement summary is an exact machine-checkable emission tied to its
candidate count and cleanup-plan digest.

Markdown:

```text
- [x] Scribe archived <N> bound cleanup <candidate|candidates>; plan <PLAN_DIGEST>
```

JSON:

```json
{
  "candidate_count": 5,
  "cleanup_plan_digest": "<PLAN_DIGEST>",
  "kind": "scribe_cleanup_summary",
  "status": "completed"
}
```

The summary must occur at a contiguous bound candidate span. A wrong count,
wrong digest, extra key, arbitrary narrative, or placement outside that span
is rejected. Detailed narrative remains in the separate Scribe cleanup note.

### Markdown structural safety

Only safe top-level list candidates can emit summaries. A candidate that owns
a continuation or nested row cannot be removed. A Markdown heading can be
deleted only when it has no protected body and the next heading is at the same
or a higher level; headings cannot emit a list summary. Baseline candidate
rows containing HTML-comment, fence, or raw HTML block controls are not
rewrite-safe.

This prevents inserted or removed structure from hiding, absorbing, or
re-parenting protected content while retaining useful deletion-only cleanup
for structurally empty heading history.

### Exact authority tokens

Authority tokens use the exact grammar:

```text
[A-Za-z][A-Za-z0-9._@/+:-]{0,159}
```

The regular expression is applied with full-string matching to the original
logical string. `value == value.strip()` is required. Quoted TASK/UNIT
scalars retain their interior value for validation, so quoted ASCII or Unicode
padding is rejected rather than normalized away. JSON owner strings follow
the same rule; leading/trailing whitespace, decoded newline controls, NBSP,
implicit non-string scalars, collections, and placeholders fail closed.

Legacy-style receipts created under a simulated trimming validator were
replayed with the repaired validator and correctly became invalid for both
TASK authorization and owner-decision paths.

## Regression Evidence

Focused final behavior coverage includes:

- comment, fence, heading, and list insertion negatives;
- protected-row deletion and candidate movement negatives;
- list-continuation and heading-body re-parenting negatives;
- arbitrary Markdown and JSON replacement negatives;
- wrong summary count and wrong plan-digest negatives;
- valid deletion-only Markdown and JSON reductions;
- valid bounded Markdown and JSON summary replacements;
- valid structurally empty heading deletion;
- record-time padded TASK, UNIT, and owner identity negatives;
- replay-time legacy padded TASK and owner identity negatives;
- exact owner no-touch, Git replacement/graft, and audit-anchor regressions
  retained from earlier repairs.

Final Scribe module suite:

```text
103 passed in 8.02s
```

Registered unit verification:

```text
177 passed in 44.74s
template-mirror: expected=84 common=84 identical=81 intentional=3 findings=0
```

Evidence:

- path:
  `reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731023129.json`
- SHA-256:
  `6f8de50c8d3a11f375dc8836173835e6727e3d75d17ae3f88cf3923323079fbe`

## Full and Supplemental Verification

Exact implementation full suite:

```text
3065 passed, 3 skipped, 4 warnings in 170.92s
```

The four warnings are the pre-existing UI console invalid-escape
`DeprecationWarning` family and are unrelated to this repair.

Supplemental gates:

| Check | Result |
| --- | --- |
| Python compile for all three portable state modules | pass |
| Three-way portable state module byte parity | pass |
| `git diff --check` | pass |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Host lock freshness | pass |
| Wheel dotfile packaging | 2 passed |
| Runtime asset usage | 38 assets, 664 uses, block 0, watch 0 |

## Live Read-only Scribe Observation

No canonical source was written. A read-only evaluation of the Runtime root
reported:

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

This is the intended fail-closed state: a fresh projection alone does not
clear overdue source debt or incomplete active-work coverage.

## Footprint and Boundary

The repair range `059bc5fb..30fdf025` changes only the six declared unit
targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/agents/scribe/SKILL.md`
- `tests/test_scribe_due.py`
- `tests/fixtures/host/agent_runtime.lock.json`

No credentials, provider calls, live network, broker/order action, database
migration, notification, consumer-repository write, version bump, tag, push,
package publication, deployment, release, merge, claim release, or W5 action
occurred.

## Fresh W4b Request

A distinct verifier must review both:

- complete implementation range:
  `ae998f7b3b96def7347be7317e3cadda6078150f..30fdf025ee3d15f88678934c827a287916f64e04`
- latest repair range:
  `059bc5fb87109eb5095960b28c30a8431e71c821..30fdf025ee3d15f88678934c827a287916f64e04`

The verifier should independently probe:

1. comment/fence/raw-HTML wrapping at candidate boundaries;
2. heading and list re-parenting, including duplicate-row ambiguity;
3. arbitrary, misplaced, miscounted, or wrong-digest summaries;
4. JSON insertions and outer-structure mutation;
5. record and replay paths for padded/control identities;
6. canonical positive Markdown, heading-deletion, JSON, and no-touch paths;
7. complete Git audit-view defenses from the earlier repair chain.

Only a fresh `APPROVE` with P0=0 and P1=0 may permit claim release and W5.
