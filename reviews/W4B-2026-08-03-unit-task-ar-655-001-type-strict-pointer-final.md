---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final
title: TASK-AR-655 Type-Strict Pointer Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T08:27:14+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: codex-independent-task-ar-655-type-strict-final-w4b
reviewer_role: independent-auditor
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: bfb326a771395199aa7371c6340dd2d81edc6ff8
candidate_tree: 20fac72e9a4e2b3d1cb2c9eaa87a1894d879ab94
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803075942.json
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
independence_status: independent_context_isolated_findings_only_lease_expired
claim_lease_status_at_authorship: expired
implementation_reviewed: true
w4b_acceptance: false
skeptic_authorized: false
release_authorized: false
claim_disposition: remain_claimed
scribe_blocker: scribe-source-debt-overdue
external_release_blockers: preserved_not_run
tags: [w4b, task-ar-655, heartbeat, renew, legacy-claim, continuity, pointer-agent, type-safety, revise]
---

# TASK-AR-655 type-strict pointer final independent W4b

## Bottom Line

`REVISE — P0: 0, P1: 1, P2: 0.`

The claim lease expired at `2026-08-03T08:26:51+09:00`, before this report
materialized at `2026-08-03T08:27:14+09:00`. Candidate identity and decisive
probes were captured while the lease was live, but this document is therefore
findings-only and cannot be treated as a valid W4b approval. Its blocking
finding independently prevents acceptance in any event.

The exact clean candidate
`bfb326a771395199aa7371c6340dd2d81edc6ff8`, tree
`20fac72e9a4e2b3d1cb2c9eaa87a1894d879ab94`, repairs the reported
response-claim presence and JSON-type-strict pointer comparison defect. It
still does not meet the registered long-running claim continuity contract:
claims created before the new mutation fields cannot heartbeat or renew. The
active TASK-AR-655 claim is a production-shaped counterexample and would be
rejected by both commands while otherwise live and owner-matched.

This context-isolated reviewer did not share the worker conversation and did
not rely on the W4a conclusion. The review was read-only except for this one
report. It did not mutate the claim, lifecycle, task/unit records, index,
production, tests, or external state; it did not run release or claim mutation
commands.

## Exact Candidate and Independent Evidence

At `2026-08-03T08:24:21+09:00`, before the claim lease deadline
`2026-08-03T08:26:51+09:00`, independent identity checks returned an empty
`git status --short`, commit `bfb326a771395199aa7371c6340dd2d81edc6ff8`,
and tree `20fac72e9a4e2b3d1cb2c9eaa87a1894d879ab94`.

Focused inspection and execution produced:

| Surface | Result |
| --- | --- |
| JSON-type-strict response-claim presence repair | pass: non-`claim_path` members require claim membership, identical concrete type, and equal value |
| Complete canonical pointer / exact revision | pass: shared field loop remains complete and mutation revision remains separately strict |
| Valid full merge / routing metadata / pointer-free overlay | pass by source and committed focused matrix |
| Focused pointer adverse/positive matrix | `74 passed, 25 deselected` in `tests/test_orchestrator_atomic_writes.py` |
| Official Verify | valid passed receipt; `874 passed, 2 skipped`; `68 passed`; mirror findings `0`; lock current; full `4597 passed, 11 skipped` |
| Task/unit/claim recurrence metadata | pass: identical 14 defect signatures and eight ordered Compound refs; newest canonical-pointer recurrence is count 4 |
| UI neutral pre-load behavior | preserved by the committed Verify/W4a evidence; no UI code changed after the passing repair |
| Existing-claim heartbeat/renew continuity | **fail / P1** |

## P1-1 — pre-field live claims cannot heartbeat or renew

`_validate_mutation_authority()` in
`src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`
requires `mutation_revision` to be a nonnegative plain integer before it will
evaluate the otherwise live owner-matched claim. `_claim_temporal_fields()`
also requires the new nested lease copies. Renewal additionally calls
`_persisted_scope_binding()`, which refuses a missing `scope_binding`. There is
no bounded compatibility initialization, migration receipt, or explicit
pre-field adoption path in either mutation command.

The active canonical claim
`agents/runtime/task_claims/CLAIM-20260803-002651-task-ar-655-5f27.json` was
created before those fields were introduced. At review time it was still
`claimed`, owner/callsite identified, and live until `08:26:51+09:00`, but it
contained neither `mutation_revision` nor `scope_binding`. Consequently:

- `heartbeat` refuses it as `claim mutation revision is invalid`;
- `renew` refuses at the same revision guard and, if only that field were
  supplied, would next refuse the missing scope binding;
- the worker therefore cannot use the feature being accepted to preserve the
  continuity of this already-running claim.

Failing closed is appropriate for ambiguous authority, but silently making all
pre-field active claims non-renewable is not the registered outcome. It
contradicts “Keep long-running task claims truthful,” the owner-checked
heartbeat/renew acceptance, and the explicit continuity purpose of TASK-AR-655.
The new-claim tests only exercise claims created by the repaired dispatcher and
therefore do not cover this boundary.

## Passing Boundaries That Do Not Override the Finding

The official receipt
`reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803075942.json` is
well-formed, attributed to the worker, contains the same five commands
registered by task and unit, and records return code zero throughout. The W4a
report correctly remains self-check evidence only. Compound closure metadata
has recurrence counts 1 through 4 and task/unit/claim parity at 14 signatures
and eight references. Scribe source-debt and active-coverage blockers remain;
native Windows CI and the named external pilots remain unrun and unauthorized.

## Required Repair and Decision

Add an explicit, atomic, owner-checked compatibility path for active claims
created before `mutation_revision`, nested temporal copies, and
`scope_binding`. It must derive only deterministic existing authority, must not
silently broaden scope, must use compare-and-swap/store-snapshot protection,
and must leave the claim byte-identical on any ambiguity or failure. Add RED
coverage from a genuinely pre-field claim for heartbeat, unchanged-scope
renewal, wrong owner, concurrent initialization, missing/ambiguous legacy
authority, and no-partial-mutation failures.

W4b acceptance is denied. Skeptic is not authorized, the claim must remain
claimed, Scribe remains a separate blocker, and no merge, release, CI, pilot,
push, tag, publish, or deployment is authorized by this review.
