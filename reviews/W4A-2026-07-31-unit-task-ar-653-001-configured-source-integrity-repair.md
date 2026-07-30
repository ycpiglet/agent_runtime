---
title: TASK-AR-653 Configured Source Integrity Repair W4a
date: 2026-07-31
created_at: 2026-07-31T03:22:00+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: de2726a6fe688e8ba81bb58a3067a7d2826664e4
repair_parent: de2726a6fe688e8ba81bb58a3067a7d2826664e4
reviewed_commit: 3887286387e8f8799edbd1ad66687c44e6fbdc32
reviewed_tree: 56f18328c09685833144bb1924b56ebc039f70e7
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..3887286387e8f8799edbd1ad66687c44e6fbdc32
repair_range: de2726a6fe688e8ba81bb58a3067a7d2826664e4..3887286387e8f8799edbd1ad66687c44e6fbdc32
worker_identity: le-20260730-234934-kst-ar653004
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-653-001-blank-structure-unique-json-final.md
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731032048.json
claim_disposition: remain_claimed_pending_fresh_independent_w4b
tags: [w4a, scribe, source-integrity, fail-closed, closure-gate, projection, repair, regression]
---

# TASK-AR-653 Configured Source Integrity Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Implementation commit
`3887286387e8f8799edbd1ad66687c44e6fbdc32` repairs the remaining P1
integration failure. A configured canonical source that is missing, unsafe,
oversized, unreadable, invalid UTF-8, malformed JSON, or duplicate-member JSON
now creates explicit source-integrity debt and blocks substantial closeout.
A newly written projection may describe that unavailable state, but cannot
turn it into a nonblocking result.

This is worker self-review and machine evidence, not independent acceptance.
Claim `CLAIM-20260730-234934-task-ar-653-ar653004` remains claimed. Claim
release, merge-queue admission, W5, versioning, publication, deployment, and
consumer mutation remain prohibited until a fresh independent W4b approves
the exact implementation commit and tree above.

## Blocking Evidence Preserved

The immutable blocking report is:

`reviews/W4B-2026-07-31-unit-task-ar-653-001-blank-structure-unique-json-final.md`

Its SHA-256 is:

`a5130faf647708520aba02ab6ad13cdd43a8c22e4ec47c251fa20cf7f4b08a23`

The report and generated index were committed separately as
`de2726a6fe688e8ba81bb58a3067a7d2826664e4` before implementation changed.
No earlier W4b evidence was edited or replaced.

## RED Before Repair

The new public evaluation, projection-write, and substantial-closeout matrix
was first run against the blocking implementation:

```text
9 failed, 1 passed, 143 deselected in 0.43s
```

The nine expected fail-open cases were:

- duplicate outer JSON collection member;
- duplicate entry identity member;
- duplicate cleanup-summary `candidate_count`;
- malformed ordinary JSON;
- invalid UTF-8;
- a source exceeding the 2 MiB parse limit;
- duplicate-member and malformed JSON after a normal projection write; and
- a substantial closure with a valid review record and duplicate-member
  configured source.

The intentionally optional, unconfigured no-source case was the one passing
case and remained advisory.

## Repair Invariants

### Configured source failures become explicit debt

`evaluate_state()` now distinguishes an intentionally absent optional source
from a source the host explicitly configured but the runtime cannot safely
interpret.

- `source-unsafe`, `source-missing`, `source-too-large`, and
  `source-parse-error` on a configured source add
  `configured-source-integrity`.
- Affected canonical paths are deduplicated and sorted under
  `source_debt.unavailable_sources`.
- The new debt field appears only when nonempty, preserving the established
  exact shape for healthy and overdue consumers.
- The integrity reason is closure-blocking and maps readiness to `blocked`.
- An owner no-touch decision cannot waive an unreadable configured source.

### Projection freshness cannot clear source integrity

`write_projection()` may still atomically persist a bounded diagnostic view,
but reevaluation retains `configured-source-integrity`, `readiness=blocked`,
and `closure_blocking=true`. The projection is evidence about canonical
state, never replacement authority for it.

### Substantial closeout gets a distinct remediation

`closure_gate.apply_scribe_obligation()` carries the unavailable source paths
into its bounded summary. For substantial, enabled closure it emits:

```text
reason=scribe-source-integrity
missing=["scribe_source_integrity"]
```

The message names the affected paths, directs the operator to repair the
configured canonical source, and states that refreshing or writing the
projection cannot clear the obligation.

Minor work and an explicitly disabled gate keep their existing policy.
Projects with neither a configured adapter nor a conventional source remain
`unavailable`/`advisory` and nonblocking.

## Regression and Compatibility Evidence

Focused integrity matrix after repair:

```text
10 passed, 143 deselected in 0.27s
```

Exact candidate Scribe and closure suites:

```text
153 passed in 10.99s
```

Final registered unit verification:

```text
206 passed in 49.30s
template-mirror: expected=84 common=84 identical=81 intentional=3 findings=0
```

Official evidence:

- path:
  `reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731032048.json`
- SHA-256:
  `713c764bd51849bfa1a6e63c280b9f96b0d8f4acc32e8bc04e1c4196b48b923b`

## Exact Candidate Full Verification

The full product suite was rerun after the implementation commit was fixed:

```text
3094 passed, 3 skipped, 4 warnings in 172.51s
```

The four warnings are the existing UI-console invalid-escape
`DeprecationWarning` family and are unrelated to this repair.

| Check | Result |
| --- | --- |
| Three-way portable state module byte parity | pass |
| Root/template closure-gate byte parity | pass |
| `git diff --check` | pass |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Host lock freshness | pass |
| Commit governance hooks | pass |

## Footprint and Boundary

Repair range
`de2726a6fe688e8ba81bb58a3067a7d2826664e4..3887286387e8f8799edbd1ad66687c44e6fbdc32`
changes exactly eight declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `scripts/closure_gate.py`
- `src/agent_runtime/templates/project/scripts/closure_gate.py`
- `tests/test_scribe_due.py`
- `tests/test_closure_gate.py`
- `tests/fixtures/host/agent_runtime.lock.json`

No credentials, provider calls, live network, broker/order action, database
migration, notification, consumer-repository write, version bump, tag, push,
package publication, deployment, release, merge, claim release, or W5 action
occurred.

## Fresh W4b Request

A distinct verifier must review both:

- complete implementation range:
  `ae998f7b3b96def7347be7317e3cadda6078150f..3887286387e8f8799edbd1ad66687c44e6fbdc32`
- latest repair range:
  `de2726a6fe688e8ba81bb58a3067a7d2826664e4..3887286387e8f8799edbd1ad66687c44e6fbdc32`

The verifier should independently probe:

1. configured missing, unsafe, oversized, unreadable, invalid UTF-8,
   malformed JSON, and duplicate-member JSON sources;
2. direct evaluation, normal projection write, and substantial closure
   composition for each relevant failure class;
3. optional no-source and healthy/overdue exact-shape compatibility;
4. the prior Markdown structure, JSON uniqueness, semantic-delta,
   exact-identity, no-touch, and Git audit-view attack families; and
5. three-way state parity, two-way closure parity, host lock, package, and
   declared footprint.

Only a fresh `APPROVE` with P0=0 and P1=0 may permit claim release and W5.
