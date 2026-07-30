---
title: TASK-AR-653 Audit View and Plan Delta Repair Independent W4b
date: 2026-07-31
created_at: 2026-07-31T02:05:15+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: f59f2d5fd68c0ad0e433228db6a41f7d58bac351
repair_parent: f59f2d5fd68c0ad0e433228db6a41f7d58bac351
reviewed_commit: 557cac333633f29860ef93d6bf28690c4b5692bc
reviewed_tree: 20350d099b1c2a8fb55dab8a3ed07bd37435c91f
w4a_evidence_head: e2204b4056cc9887fcfb22e54e9c74c25463f705
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..557cac333633f29860ef93d6bf28690c4b5692bc
repair_range: f59f2d5fd68c0ad0e433228db6a41f7d58bac351..557cac333633f29860ef93d6bf28690c4b5692bc
verifier_agent_instance_id: qa-20260731-ar653-audit-view-plan-delta-final-w4b
verified_by: qa-20260731-ar653-audit-view-plan-delta-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_audit_view_plan_delta_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
prior_verifier_identity: qa-20260731-ar653-git-audit-anchor-final-w4b
independence_status: independent
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
tags: [w4b, scribe, audit-view, identity-token, cleanup-plan, independent-verification, revise]
---

# TASK-AR-653 Audit View and Plan Delta Repair Independent W4b

## Independent Verdict

`REVISE — P0: 0, P1: 2, P2: 0.`

Candidate `557cac333633f29860ef93d6bf28690c4b5692bc` closes the
repository replacement/graft/lazy-fetch finding and the exact owner
`no_touch` finding. Its registered verification suite is green, and valid
Markdown and JSON reductions still work.

Two stronger correctness bypasses remain:

1. inserted Markdown structure can semantically hide a plan-excluded row while
   the row's raw bytes still satisfy the ordered-subsequence check; and
2. TASK/UNIT and JSON owner identities are trimmed before validation, so the
   raw committed values need not obey the declared exact ASCII-token grammar.

Both can produce a closure-ready outcome from evidence that violates the
declared Scribe contract. An `APPROVE` requires P0 and P1 both to be zero, so
this candidate is not a release credential.

## Exact Reviewed State and Independence

| Identity | Exact value |
| --- | --- |
| Complete review base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Blocking `REVISE` evidence / repair parent | `f59f2d5fd68c0ad0e433228db6a41f7d58bac351` |
| Reviewed implementation | `557cac333633f29860ef93d6bf28690c4b5692bc` |
| Reviewed implementation tree | `20350d099b1c2a8fb55dab8a3ed07bd37435c91f` |
| W4a/evidence HEAD | `e2204b4056cc9887fcfb22e54e9c74c25463f705` |
| W4a/evidence HEAD tree | `12e724188fc3952c608100eed119bb3a3e43e810` |
| Verifier | `qa-20260731-ar653-audit-view-plan-delta-final-w4b` |
| Verifier task | `/root/task_ar_653_audit_view_plan_delta_final_w4b` |
| Worker | `le-20260730-234934-kst-ar653004` |

This verifier is a distinct agent instance with independent conversation
context and did not share the worker identity. The worktree was clean at
review start. The verifier reviewed both
`f59f2d5f..557cac33` and `ae998f7b..557cac33`, read the prior blocking W4b
and the fresh W4a, and did not edit implementation, claim, unit, lifecycle,
index, consumer repositories, or existing evidence. This report is the only
new repository file created by the verifier.

## P1-1 — Raw-Line Subsequence Does Not Preserve Markdown Meaning

The repair reconstructs the committed baseline and correctly prevents direct
deletion or replacement of a plan-excluded Markdown line. It then defines
preservation as:

```text
protected baseline nonblank lines form an ordered subsequence of after lines
```

That condition preserves raw line strings, but not their Markdown context,
visibility, or meaning. Inserted control rows are unrestricted.

### Minimal independent reproduction

The verifier created an offline temporary Git repository with:

- 16 hot Markdown rows;
- one `- TASK-SCRIBE active record` row excluded from the cleanup plan as an
  active reference; and
- five ordinary rows that were valid bound cleanup candidates.

The after-source deleted only those five candidates but inserted an HTML
comment boundary around the excluded active row:

```markdown
# Status
<!--
- TASK-SCRIBE active record
-->
- item 5
...
- item 14
```

The exact protected line remains an ordered subsequence, so both record-time
validation and the immediate receipt replay accepted the source:

```json
{"cleanup":"verified_reduction","hot":11,"readiness":"ready"}
```

CommonMark renders the active record inside the HTML comment as hidden. The
canonical row is therefore semantically removed from the document even though
its raw line bytes remain. The receipt authorizes a false ready outcome.

The same focused matrix also confirmed that the current validator accepts:

- a new Markdown heading outside the candidate source orders, returning
  `verified_reduction`, `hot=11`, `readiness=ready`;
- a new JSON entry
  `{"id":"TASK-INSERTED-OUTSIDE-PLAN","status":"open"}`, returning the same
  ready result; and
- moving an allowed candidate across two protected rows while preserving only
  the protected rows' relative order, returning a valid reduction.

Plain insertion is not counted as a separate finding because an authorized
candidate replacement may legitimately add one bounded archive summary.
Likewise, relative movement around a candidate is not independently decisive.
The stronger failure is that insertion has no structural or semantic boundary:
it can hide or recontextualize protected Markdown content. The arbitrary JSON
entry demonstrates the same absence of an enforced “bounded archive summary”
constraint, but the Markdown semantic-hiding case is sufficient to block
acceptance.

### Required invariant and repair

- A plan-excluded Markdown node must remain visible and retain its structural
  context, not merely reappear as the same raw line somewhere in the file.
- Insertions and replacement output must be bound to candidate source spans
  and to a defined, bounded summary form.
- Inserted HTML blocks/comments, fenced-code boundaries, headings, list
  nesting, or other structure must not absorb, hide, or re-parent protected
  nodes.
- Enforce the same invariant at receipt record and replay.
- Add negative regressions for comment wrapping, fenced-code wrapping,
  heading/list re-parenting, and insertions outside candidate spans, plus
  positive Markdown and JSON summary replacements.

## P1-2 — Identity Validation Accepts Non-Token Raw Evidence

The declared authority grammar is:

```text
[A-Za-z][A-Za-z0-9._@/+:-]{0,159}
```

The implementation applies that regular expression only after calling
`strip()`. TASK/UNIT frontmatter is also stripped while removing quotes.
Consequently, the raw committed evidence can contain whitespace or decoded
control characters that the grammar and Scribe skill explicitly forbid.

### Minimal independent reproductions

All of these exact raw identity forms were accepted and produced valid
closure outcomes:

| Surface | Raw logical value | Accepted outcome |
| --- | --- | --- |
| TASK authorization | `" lead-engineer-fixture "` | `verified_reduction` |
| JSON owner decision | `" owner-fixture "` | `owner_decision` |
| JSON owner decision | `"owner-fixture\n"` | `owner_decision` |
| JSON owner decision | NBSP + `owner-fixture` + NBSP | `owner_decision` |

The JSON newline is serialized as a control escape and decoded before
validation. Trimming turns it into `owner-fixture`, contradicting the prior
W4b's explicit requirement to reject control-escape and other non-token forms
regardless of quoting. Immediate replay validates the same non-token committed
identity and leaves the outcome ready.

This is not only presentation drift. Other evidence consumers may compare the
raw principal exactly, making `owner-fixture`, ` owner-fixture `, and
`owner-fixture\n` different identities while this gate treats them as one.
The committed approver identity is therefore not a stable token.

### Required invariant and repair

- Validate the exact raw logical identity value without trimming or Unicode
  whitespace normalization.
- Require `value == token` and the ASCII-token regex to match the entire raw
  value.
- Reject all leading/trailing ASCII or Unicode whitespace and all control
  characters on TASK, UNIT, and JSON owner surfaces.
- Keep quoted canonical tokens valid only when unquoting yields exactly the
  token; reject escaped or padded values.
- Apply the rule at record and replay, with positive coverage for canonical
  Runtime identities and negative coverage for whitespace/control cases.

## Closed Families and Positive Paths

### Canonical local Git audit view

The repair consistently strips inherited `GIT_*` variables and supplies
`GIT_NO_REPLACE_OBJECTS=1`, `GIT_NO_LAZY_FETCH=1`,
`GIT_OPTIONAL_LOCKS=0`, and `GIT_TERMINAL_PROMPT=0`. It rejects
`refs/replace` and non-empty, non-regular, or symlinked graft state before
audit reads.

Registered replacement/graft record and replay regressions passed. An
additional offline partial-clone simulation removed a promised blob and used a
local fake remote helper:

```json
{
  "audit_read": "failed-closed",
  "fetch_attempt_with_no_lazy": false,
  "control_fetch_attempt_without_no_lazy": true
}
```

This proves the audit read failed locally without invoking the helper, while
the sensitivity control did invoke it when lazy-fetch suppression was removed.
No network was used.

### Exact owner `no_touch`

Record time now requires the complete after-source binding list and hot count
to equal the baseline. Replay independently requires the receipt's
after-bindings/current sources and resulting count to equal the same baseline.
The registered exact no-touch positive path passed; same-count rewrite,
increase, and rebound replay negatives passed.

### Direct plan-delta protection and valid reductions

Registered Markdown and JSON protected-row deletion negatives and the rebound
replay negative passed. A legitimate Markdown reduction passed in the
registered suite. An additional legitimate JSON reduction independently
returned:

```json
{
  "record": "verified_reduction",
  "replay": "verified_reduction",
  "hot": 11,
  "readiness": "ready"
}
```

These positive results show that P1-1 is the structural insertion bypass, not
a blanket failure of valid bounded reductions.

## Verification Evidence

| Check | Independent result |
| --- | --- |
| Exact implementation commit/tree | matched `557cac33` / `20350d09` |
| Registered unit pytest command | `151 passed in 41.65s` |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Live read-only Scribe evaluation | hot 773, overdue, projection fresh, coverage incomplete, cleanup none, blocked |
| Three portable state-projection copies | byte-identical |
| Complete implementation `git diff --check` | pass |
| Offline lazy-fetch sensitivity test | audit failed closed; no helper invocation |
| Valid JSON record/replay positive | verified reduction / verified reduction |
| Markdown semantic-hiding probe | incorrectly accepted as ready |
| TASK/owner whitespace-control probes | incorrectly accepted |
| Worktree before report | clean |

Registered command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_scribe_due.py tests/test_closure_gate.py \
  tests/test_session_continuity_hooks.py tests/test_doctor.py \
  tests/test_template_smoke.py -q -p no:cacheprovider
```

The independent run agrees with W4a's machine evidence that the registered
suite and mirror gate are green. It does not treat that green suite as proof
against the two stronger behavior cases above.

## Boundary and Claim Disposition

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, release,
merge, or consumer-repository action was performed.

Claim `CLAIM-20260730-234934-task-ar-653-ar653004` must remain `claimed`.
This exact candidate must not be released, enter the merge queue, or advance to
W5. A repaired implementation needs focused RED/GREEN regressions, a fresh
W4a bound to its exact commit/tree, and another distinct independent W4b with
P0=0 and P1=0.
