---
title: TASK-AR-653 Scribe Git Audit Anchor Repair W4a
date: 2026-07-31
created_at: 2026-07-31T01:20:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
reviewer: le-20260730-234934-kst-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
second_revise_evidence_commit: 1440ab4ec1370c3b4887efedcc4ac668c4cfeaa7
candidate_commit: 74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f
candidate_tree: 9624446dc6f11c2373130abe51e375f4977768ab
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731011752.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-653-001-receipt-authority-repair.md
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-receipt-authority-repair.md
tags: [w4a, scribe, cleanup-receipt, git-audit-anchor, authority, repair, regression]
---

# TASK-AR-653 Scribe Git Audit Anchor Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f` repairs both P1
findings in the second independent `REVISE`:

1. a mutable projection, receipt, and live authorization can no longer be
   coherently rebound into false historical evidence; and
2. non-scalar or placeholder approver values and conflicting TASK/UNIT
   identities can no longer authorize cleanup.

This is worker self-review, not acceptance. Both earlier W4a reports and both
independent `REVISE` reports remain immutable history. The claim stays
`claimed` until a distinct verifier reviews this exact candidate and returns a
fresh W4b `APPROVE` with P0/P1 both zero.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Review base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Second `REVISE` evidence commit | `1440ab4ec1370c3b4887efedcc4ac668c4cfeaa7` |
| Repaired implementation | `74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f` |
| Repaired tree | `9624446dc6f11c2373130abe51e375f4977768ab` |
| Worker | `le-20260730-234934-kst-ar653004` |
| Claim | `CLAIM-20260730-234934-task-ar-653-ar653004` |
| Repair footprint | 9 declared paths changed, 0 undeclared |

The nine repair paths are the three byte-identical state-projection copies,
the Scribe CLI source/template pair, the packaged Scribe skill, the host-lock
fixture, and the two registered test files. No consumer repository or
host-owned canonical state was modified.

## RED: Stronger Independent Attacks

The second W4b proved that internally consistent checksums were not an
independent trust anchor. It could:

- change an unchanged source's declared hot count from 11 to 16, recompute all
  nested bindings, and obtain a false reduction;
- change a legitimate receipt's historical count from 16 to 99, rebind the
  live authorization and outer digest, and keep the receipt valid;
- use JSON objects as owner identities;
- use YAML null/boolean/collection/number values as Scribe identities; and
- declare `id: TASK-UNRELATED` while retaining a matching `work_id`.

The initial second-repair RED selection produced `8 failed, 42 deselected`.
The final regression matrix expands those cases to comment-suffixed YAML
placeholders, UNIT parent disagreement, owner authority, and post-receipt live
authority rewrites.

## GREEN: Immutable Baseline and Authority Evidence

Cleanup recording now requires a local Git audit anchor:

- the active TASK/UNIT authorization must byte-match its latest committed
  blob;
- that commit must be reachable from the current `HEAD`;
- every baseline source is loaded from that exact commit, with a regular-file
  mode and bounded size;
- Markdown/JSON source bytes are parsed again, and their SHA-256, hot count,
  selected window, cleanup candidates, exclusions, source fingerprints, and
  cleanup-plan digest are recomputed;
- the receipt stores the baseline commit, authorization commit, and
  authorization blob OID; and
- replay reads the stored Git object instead of trusting the mutable current
  authorization file.

An owner no-touch decision has the same committed-blob requirement. Its commit
must descend from the authorization commit, and the baseline source and plan
must still reproduce at that decision commit. Reduction receipts must carry
null owner-decision anchor fields. The receipt schema rejects missing or extra
fields.

This supports the intended sequence: generate the projection, bind and commit
authorization while baseline source bytes still exist, perform the separately
authorized canonical edit, then record the receipt. A later edit to the live
authorization neither rewrites history nor invalidates the receipt; replay
continues to use the original committed blob.

## GREEN: Strict Identity Boundary

Authority parsing no longer coerces arbitrary values through `str()`:

- owner `approved_by` must be an actual JSON string;
- Scribe identity must be an explicit bounded string, not null, boolean,
  number, collection, YAML anchor/tag, or placeholder;
- inline YAML comments are stripped outside quoted scalars before ambiguity
  checks;
- TASK `id` and `work_id` must both equal the file stem; and
- UNIT `work_id`/`unit_id` must equal the file stem, while
  `task_id`/`parent_id` must both equal the parent TASK directory.

Duplicate recognized frontmatter fields and duplicate JSON object members
remain fail-closed. The valid canonical TASK, UNIT, reduction, and owner
no-touch paths all remain covered.

## Positive and Negative Proof

Registered tests demonstrate:

- a fully rebound unchanged-source baseline is rejected;
- a fully rebound receipt plus new live authorization is rejected;
- an authority commit not tied to the committed source bytes cannot replace
  the receipt's historical baseline;
- object, list, null, boolean, numeric, placeholder, and comment-suffixed
  ambiguous approver identities are rejected;
- conflicting TASK IDs and either conflicting UNIT parent field are rejected;
- a canonical UNIT authorization records a valid reduction;
- a legitimate owner no-touch decision remains valid; and
- rewriting and committing the live authorization after a valid receipt does
  not change which authority blob replay evaluates.

## Live Read-Only State

The current Runtime checkout still reports, without writing a projection or
receipt:

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

The audit-anchor repair therefore does not weaken the original four-axis
Scribe closure semantics.

## Verification

| Verification | Result |
| --- | --- |
| Final full Runtime suite at exact implementation commit | `3020 passed, 3 skipped, 4 known UI warnings` in `163.80s` |
| Registered work-verification suite | `132 passed` in `38.99s` |
| Focused Scribe suite | `58 passed` |
| Template/package/Scribe integration slice | `78 passed` |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Runtime asset usage gate | 38 assets, 557 uses, 0 block, 0 watch |
| Wheel dotfile packaging | pass, 7 required entries |
| Host lock current check | pass |
| Three-way state-projection byte comparison | pass |
| Scribe CLI source/template byte comparison | pass |
| `git diff --check` | pass |

The four warnings are the existing UI route-sweep invalid-escape deprecation
warnings. No test failed.

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731011752.json`
(SHA-256
`10ccadb0f0bef0030334b3534ae485243aa5a91fb6819fe3af23f06a710b68bf`)
binds the registered 132-test suite and mirror gate. Older verification files
belong to superseded candidates and are not acceptance evidence for this
repair.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, or release
action occurred. Bean Wiki, Allimbot, and Autofolio remain untouched pending
the Runtime hardening sequence and observation-only pilots.

Request a fresh independent W4b over implementation range
`1440ab4ec1370c3b4887efedcc4ac668c4cfeaa7..74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f`
and complete review range
`ae998f7b3b96def7347be7317e3cadda6078150f..74a82b2bf1bfa5a3476e059c34aaa1a02bd7164f`.
Only an independent `APPROVE` permits claim release and local W5 integration.
