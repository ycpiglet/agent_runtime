---
title: TASK-AR-653 Scribe Audit View and Plan Delta Repair W4a
date: 2026-07-31
created_at: 2026-07-31T01:52:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
reviewer: le-20260730-234934-kst-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
repair_parent: f59f2d5fd68c0ad0e433228db6a41f7d58bac351
candidate_commit: 557cac333633f29860ef93d6bf28690c4b5692bc
candidate_tree: 20350d099b1c2a8fb55dab8a3ed07bd37435c91f
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731015019.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-653-001-git-audit-anchor-repair.md
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-git-audit-anchor-repair.md
tags: [w4a, scribe, audit-view, no-touch, authority, cleanup-plan, repair, regression]
---

# TASK-AR-653 Scribe Audit View and Plan Delta Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `557cac333633f29860ef93d6bf28690c4b5692bc` repairs all four
P1 findings in the third independent `REVISE`:

1. repository-local Git replacement and graft state can no longer change the
   cleanup audit view;
2. owner `no_touch` now means byte-equivalent source bindings, not merely a
   non-decreasing hot count;
3. TASK/UNIT and owner approver identities share one unambiguous token grammar;
   and
4. a reduction may delete or replace only baseline rows named by its bound
   cleanup plan.

This is worker self-review, not acceptance. The prior W4a and independent
`REVISE` reports remain immutable history. The claim stays `claimed` until a
distinct verifier reviews this exact candidate and returns a fresh W4b
`APPROVE` with P0/P1 both zero.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Review base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Third `REVISE` evidence commit | `f59f2d5fd68c0ad0e433228db6a41f7d58bac351` |
| Repaired implementation | `557cac333633f29860ef93d6bf28690c4b5692bc` |
| Repaired tree | `20350d099b1c2a8fb55dab8a3ed07bd37435c91f` |
| Worker | `le-20260730-234934-kst-ar653004` |
| Claim | `CLAIM-20260730-234934-task-ar-653-ar653004` |
| Repair footprint | 6 declared paths changed, 0 undeclared |

The six paths are the three byte-identical state-projection copies, the
packaged Scribe skill, the generated host-lock fixture, and the registered
Scribe test file. No consumer repository or host-owned canonical state was
modified.

## RED to GREEN

The initial focused RED selection reproduced every reported family:

```text
12 failed, 8 passed, 50 deselected in 1.73s
```

The failures covered:

- owner-approved same-count rewrites and source growth;
- repository-local replacement and graft views;
- Markdown deletion of an active TASK row;
- JSON deletion of a canonical REVIEW entry; and
- hexadecimal, special-float, date-like, sexagesimal, and escaped identity
  forms.

After the repair, the focused record-time matrix passed `22/22`. Replay
regressions then proved that recomputing projection fingerprints, receipt
after-bindings, resulting counts, and the receipt digest does not restore a
ready outcome after an unplanned row removal, a no-touch source rewrite, or an
active replacement view.

## P1-1 Closure — Canonical Local Git Audit View

Every cleanup audit subprocess now:

- removes inherited `GIT_*` state;
- sets `GIT_NO_REPLACE_OBJECTS=1`;
- sets `GIT_NO_LAZY_FETCH=1`;
- disables optional locks and terminal prompts; and
- rejects any repository-local `refs/replace` entry or non-empty/symlinked
  graft state before reading commits, trees, blobs, path history, or ancestry.

Record-time failures remain explicit. Receipt replay converts the same
condition into an invalid, closure-blocking cleanup outcome. The object reads
therefore remain local, read-only, and independent of repository replacement
configuration.

## P1-2 Closure — Exact Owner No-Touch

For a valid owner decision, the complete after-source binding list must equal
the baseline list exactly:

- adapter and path;
- presence;
- source SHA-256; and
- source hot count.

Record-time same-count rewrites and increases are rejected. Replay independently
requires the receipt's current after-bindings and resulting hot count to equal
the anchored before state. The existing byte-identical owner-decision positive
path remains green.

## P1-3 Closure — One Authority Identity Grammar

Both `scribe_authorized_by` and owner `approved_by` now require an ASCII token:

```text
[A-Za-z][A-Za-z0-9._@/+:-]{0,159}
```

Placeholder words remain forbidden. The leading-letter rule excludes numeric,
hexadecimal, special-float, date, and sexagesimal implicit scalars. The
allowlist excludes collection syntax, YAML tags/anchors, backslash escapes,
control characters, and whitespace. Existing Runtime identities such as
`lead-engineer-fixture` and `owner-fixture` remain valid.

## P1-4 Closure — Plan-Bound Source Delta

For every changed source, validation loads the baseline bytes from the stored
commit and re-reads the bounded current file while checking its recorded
digest.

- Markdown uses the cleanup plan's exact baseline `source_order` values.
  Every other nonblank baseline row must survive unchanged and in order.
- JSON requires the same selected collection and identical surrounding
  structure. Every non-candidate entry must survive unchanged and in order.
- A changed source with no bound candidates is rejected.
- The same reconstruction runs both while recording and while replaying a
  reduction receipt.

Insertions remain possible for a bounded archive summary, but they cannot make
an excluded baseline row disappear. Aggregate hot-count reduction and
self-consistent receipt digests are no longer sufficient.

## Positive and Negative Proof

Registered tests demonstrate:

- replacement refs and grafts fail closed at record time;
- a stored receipt becomes invalid while a replacement view exists;
- valid local Git object replay and post-receipt live authority rewrites still
  work;
- exact owner no-touch remains valid while rewrites and increases fail;
- TASK/UNIT and JSON owner identity ambiguity is rejected by the same grammar;
- active TASK and canonical REVIEW rows cannot be removed from Markdown or
  JSON sources unless present in the anchored plan;
- coherently rebound projection and receipt metadata cannot hide a later
  protected-row deletion;
- legitimate Markdown reduction and canonical UNIT authorization remain valid;
  and
- canonical/template/portable projection code stays byte-identical.

## Live Read-Only State

The current Runtime checkout still reports, without writing a projection,
receipt, or canonical state:

```text
hot_count=773
source_debt.status=overdue
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

The repair therefore preserves the original four-axis Scribe closure
semantics and does not convert the Runtime's own overdue source into a false
ready state.

## Verification

| Verification | Result |
| --- | --- |
| Full Runtime suite at exact implementation commit | `3039 passed, 3 skipped, 4 known UI warnings` in `162.69s` |
| Registered work-verification suite | `151 passed` in `41.38s` |
| Focused Scribe plus template smoke suite | `89 passed` |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Runtime asset usage gate | 38 assets, 592 uses, 0 block, 0 watch |
| Wheel dotfile packaging | pass, 7 required entries |
| Host lock current check | pass |
| Three-way state-projection byte comparison | pass |
| Python bytecode compilation | pass |
| `git diff --check` | pass |

The four warnings are the existing UI route-sweep invalid-escape deprecation
warnings. No test failed.

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731015019.json`
(SHA-256
`6f6600d59eebf895d2c915c37735b3cbaccf2d23c32985871e47814f70ff262c`)
binds the registered 151-test suite and mirror gate. Older verification files
belong to superseded candidates and are not acceptance evidence for this
repair.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, or release
action occurred. Bean Wiki, Allimbot, and Autofolio remain untouched pending
the Runtime hardening sequence and observation-only pilots.

Request a fresh independent W4b over implementation range
`f59f2d5fd68c0ad0e433228db6a41f7d58bac351..557cac333633f29860ef93d6bf28690c4b5692bc`
and complete review range
`ae998f7b3b96def7347be7317e3cadda6078150f..557cac333633f29860ef93d6bf28690c4b5692bc`.
Only an independent `APPROVE` permits claim release and local W5 integration.
