---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-w4b-type-strict-pointer-t3-replan
title: TASK-AR-655 W4b Type-Strict Pointer Authority T3 Amendment
date: 2026-08-03
created_at: 2026-08-03T07:38:03+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
score: 100
verdict: ACCEPT_W4B_TYPE_STRICT_POINTER_REPAIR
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: c877b0b6bc50c3ba925c9562a82897df7a3bb833
candidate_tree: ead19cfacd1b3b2dbe3dbcccac02ca7c41873cd0
defect_signature: defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe
recurrence_status: three_canonical_matches_found_pre_red
post_green_compound_obligation: recurrence_count_4
release_authorized: false
tags: [task-ar-655, t3-replan, w4b, recurrence, pointer-agent, type-safety, fail-closed]
---

# TASK-AR-655 W4b type-strict pointer authority T3 amendment

## Bottom Line

Accept the context-isolated W4b P1. The complete field-name binding repair is
structurally correct, but ordinary Python equality still acknowledges JSON
type aliases and `dict.get()` launders absent committed-claim members through
projected `null`. The UI repair passes and is not reopened.

Exact canonical Compound search with legacy fallback disabled returned the
same projection-binding signature at recurrence counts 1, 2, and 3. This is a
fourth occurrence of
`defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe`,
not a new defect signature. Keep all three records immutable and append count
4 only after test-first repair and fresh GREEN Verify.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| W4b finding | accepted P1 | float/int, bool/int, and absent-claim/`null` receipts returned success |
| Compound classification | recurrence | exact counts `1`, `2`, `3`; legacy fallback disabled |
| UI pre-load truthfulness | pass, preserved | desktop/mobile delayed, 503, abort, and timestamp probes pass |
| Verification | failed pending repair | prior full Verify remains evidence, not approval for the counterexample |
| Release | blocked | W4b acceptance, skeptic, Scribe, and external boundaries remain closed |

## Action

Follow this failure-first sequence:

1. Commit the W4b report, this accepted amendment, exact lookup result, and
   verification-failed lifecycle state before changing tests or production.
2. In a separate test-only commit, extend the production-shaped progress
   matrix with same-numeric JSON type aliases for `progress_pct`, `step_index`,
   and `step_total`, including boolean/integer aliases.
3. Add missing-response-claim cases for every non-`claim_path` member of the
   shared canonical tuple. Keep the projected key present as `null` and
   require bounded indeterminate failure.
4. For every adverse row require exit `2`,
   `claim_progress_receipt_indeterminate`, `commit_state: unknown`,
   `retry_safe: false`, and byte-identical claim and pointer sentinels.
5. Preserve valid full merge, all supplementary routing metadata, exact
   mutation revision, pointer-free overlays, and the passing UI behavior.
6. Implement one shared exact-value predicate in the orchestrator validator:
   each non-`claim_path` member must exist in the response claim, candidate and
   expected JSON types must be identical, and values must be equal. Continue
   binding `claim_path` to the canonical ref and revision through its strict
   integer check.
7. Refresh only registered mirrors/host lock if the production footprint
   requires it, run the exact REDs, complete orchestrator and registered
   verification chains, and run a fresh official Verify.
8. Append recurrence count 4, restore lifecycle evidence, produce a new W4a,
   and require another context-isolated W4b. A skeptic remains forbidden until
   that future W4b passes.

## Acceptance Contract

- JSON integer, float, and boolean values are never mutually substitutable in
  canonical pointer authority, even when Python considers them equal.
- Every shared canonical member except synthetic `claim_path` is explicitly
  present in the committed response claim; absence cannot become an expected
  `None` through `dict.get()`.
- A legitimately present `null` value may match only a projected `null`, while
  schema and identity/status guards retain their existing restrictions.
- Every mismatch is bounded, indeterminate, non-retryable, and read-only.
- The full production projection still contains all 22 canonical members and
  preserves supplementary routing fields.
- Overlay receipts remain pointer-free; valid full merge and exact revision
  behavior remain unchanged.
- Neutral desktop/mobile UI output before delayed or failed Runtime state and
  real output after successful arrival remain unchanged.

## Risks / Blockers

The active unit returns to verification-failed and the claim remains held.
Existing 14/14 Compound coverage records the known history but cannot approve
this reproduced recurrence; count 4 is forbidden until fresh GREEN Verify.

The separate Scribe `source-debt-overdue` and `active-coverage-incomplete`
blockers remain unwaived. No skeptic, task close, claim release, merge,
consumer pilot, CI dispatch, push, tag, version, package, publication,
deployment, or other external action is authorized.

## Decision

Accept the W4b finding and authorize only the bounded failure-first validator
repair described above. Do not reopen the independently passing UI repair and
do not broaden into claim schema redesign or consumer migration.

## Next Steps

Commit this amendment and lifecycle state, then capture the type-strict and
missing-response-claim REDs in a separate test-only commit. Stop before any
production edit until that RED commit is independently inspectable.
