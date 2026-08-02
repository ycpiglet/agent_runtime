---
schema_version: agent-runtime-review/v1
id: W4A-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final
title: TASK-AR-655 Projection-Binding Repair Final W4a
date: 2026-08-03
created_at: 2026-08-03T05:05:01+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4a
reviewer: le-20260803-001200-kst-ar655lease001
reviewer_role: lead-engineer
status: passed
signal: pass
verdict: PASS_PENDING_DISTINCT_W4B_SKEPTIC_AND_SCRIBE
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 0236a9f95910fe5d09b6eb12496dace82147d166
candidate_tree: 4985d67fe4174aa8c91c7f374fc55e4ab56d538c
accepted_replan_commit: 42222a24a148060e6f280cb69311111f26ac91f8
red_commit: b4e6d7829fb11cff3c2535d9c642a842477a6eef
implementation_commit: 1239d0322ea3b9ea2631d31e31ff7c868fbde1d2
implementation_tree: e926b684f781c41405aefd3a76964f0f6b1a4732
implementation_range: 42222a24a148060e6f280cb69311111f26ac91f8..1239d0322ea3b9ea2631d31e31ff7c868fbde1d2
evidence_commit: 0236a9f95910fe5d09b6eb12496dace82147d166
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803045245.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260803-050159-bind-claim-progress-projection-to-committed-clai-2398011ac247.json
source_w4b: reviews/W4B-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
replan_ref: reviews/REVIEW-2026-08-03-task-ar-655-w4b-projection-binding-t3-replan.md
independence_status: worker_self_check_only
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_fresh_independent_w4b_skeptic_and_scribe
scribe_blocker: preserved_unresolved
external_release_blockers: preserved_not_run
tags: [w4a, task-ar-655, claim-progress, receipt, projection, pointer, overlay, compound, repair]
---

# TASK-AR-655 projection-binding repair final W4a

## Verdict

`PASS_PENDING_DISTINCT_W4B_SKEPTIC_AND_SCRIBE — P0: 0, P1: 0, P2: 0`.

Exact evidence candidate `0236a9f95910fe5d09b6eb12496dace82147d166`,
tree `4985d67fe4174aa8c91c7f374fc55e4ab56d538c`, contains the bounded
repair for the prior independent W4b's P1 and fresh durable verification plus
Compound evidence. The worker self-check found no remaining current-scope
finding.

This is not independent approval. `w4b_acceptance` remains false, the active
claim remains `claimed`, and release is not authorized. A new context-isolated
W4b must review the exact post-W4a candidate. Only after that reviewer returns
without P1 may a different skeptic review run.

## Exact repair chain

The committed chain is linear:

```text
42222a24  accept the W4b projection-binding repair scope
b4e6d782  commit the conflicting-projection RED regression
073ee1bb  record the failure-first lifecycle state
1239d032  bind claim-progress projection authority and update the managed lock
79083ae0  record the repair SHA, tree, and local GREEN results
0236a9f9  record fresh Verify, append-only Compound, and lifecycle evidence
```

Source and test changes stop at implementation commit
`1239d0322ea3b9ea2631d31e31ff7c868fbde1d2`, tree
`e926b684f781c41405aefd3a76964f0f6b1a4732`. Later commits change only
registered lifecycle and durable evidence surfaces. The worktree was clean
before this review file was created.

## P1 repair audit

The prior W4b proved that a zero-exit dispatcher response could combine the
correct claim ID and next revision with a projection naming a different task,
unit, task set, claim reference, current agent, and primary pointer. The RED
test at `b4e6d782` reproduced that exact acknowledgement as one failure: actual
exit `0`, required bounded-indeterminate exit `2`.

The repaired validator now requires all of the following before returning
success:

1. response `path` and projection `task_claim_ref` equal the canonical active
   claim path;
2. projection task, optional unit, and optional task-set identities exactly
   equal the committed claim identities;
3. a merge projection applies only to a non-overlay claim and contains a
   primary pointer with the same active task, active task set, and sole active
   claim reference;
4. that pointer contains exactly one current-agent entry with the same claim,
   identities, and exact committed mutation revision; and
5. an explicit overlay accepts only `overlay-no-primary-pointer`, requires the
   committed claim to be an overlay, and rejects any invented `pointer` key.

Any zero-exit response that fails this binding follows the existing bounded
indeterminate contract: non-success, `commit_state: unknown`,
`retry_safe: false`, and no orchestrator-side claim or pointer mutation.

The final test file has 16 passing cases, including the original conflicting
merge projection and a parameterized valid-versus-invented overlay pointer
boundary. The earlier committed RED is preserved; it was not rewritten.

## Fresh verification evidence

The fresh Verify artifact is
`reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803045245.json`, SHA-256
`345edbe5f053ff8a3352d46ba519efa8d7f4b09fb66c7afa90a556de884fb624`.
It is attributed to the active worker and records exactly five commands, all
with `status: passed` and return code `0`:

| Registered command | Durable result |
| --- | --- |
| Primary lease/claim/consumer suite | `789 passed, 2 skipped` |
| Mirror and managed-host suite | `68 passed` |
| Template mirror gate | `86` common, `83` identical, `3` intentional, findings `0` |
| Managed host lock check | current |
| Complete repository suite | `4506 passed, 11 skipped, 4 known UI warnings` |

The four warnings are the existing `invalid escape sequence '\\/'`
deprecation warnings from the UI route-sweep test. Evidence index validation
passes with zero findings. Work schema validation has zero findings and 19
unrelated legacy warnings.

## Compound and recurrence truth

The repair Compound is append-only and has SHA-256
`c9286c7a10b06ca9ff2c22ab3285cb5c9655ef690d3c5f45d46ba1fdbb5e8694`.
It links the prior W4b, accepted replan, production validator, regressions, and
fresh Verify to the new signature. The two earlier records remain byte-stable
at hashes `382334aacedd2e671cabdf09c618964412ccff3c5ef5ba6a142dd44e7ac6538e`
and `b4002b45440f8b045e0c7c7a96c2835e0c5aa44519897af57b2cdb4a680e0d99`.

Task, unit, and active claim have the same 12 signatures and three Compound
references. Their linked-record union covers all 12 with no uncovered or
extraneous signature. `compound_record.py check` passes, and the closure gate
reports repeated-failure authority `required: true`, `satisfied: true`, with an
empty findings list.

## Blockers deliberately retained

Closure still returns `decision: block` with
`reason: scribe-source-debt-overdue`. Its only missing obligations are
`scribe_source_debt` and `scribe_active_coverage`; `STATUS.md` remains overdue
and the bounded projection does not represent the current task and claim set.
That separately owned cleanup is outside this repair and has not been waived.

Native Windows CI and the Bean Wiki, Allimbot, and Autofolio pilots were not
run from this worktree. No consumer repository was mutated. Those remain later
release gates; Basketball Platform remains out of scope.

## Independent review request

The fresh W4b must inspect the exact post-W4a commit and tree, review
`42222a24..1239d032`, validate the fresh Verify and all three Compound records,
and independently probe at least:

- conflicting response path and claim reference;
- task, optional unit, and task-set mismatch or malformed identity;
- missing, multiple, stale-revision, or conflicting current-agent entries;
- primary-pointer task, task-set, and active-claim mismatch;
- merge-versus-overlay operation confusion; and
- an overlay response that invents any primary pointer.

It must preserve the Scribe and external-release blockers. Any current-scope P1
returns the unit to failed. After a W4b pass, a different skeptic must attempt
cross-component counterexamples before any release decision.

## Safety boundary

No credential, live provider, network package installation, broker, order,
database migration, notification, consumer mutation, CI dispatch, version
bump, tag, package publication, push, deployment, claim release, task close,
merge, or external release action occurred or is authorized by this W4a.
