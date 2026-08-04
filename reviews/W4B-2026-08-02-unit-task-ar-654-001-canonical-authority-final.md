---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final
title: TASK-AR-654 Canonical Authority Final Independent W4b
date: 2026-08-02
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: w4b
status: blocked
signal: fail
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 3, P2: 0}
candidate_commit: c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9
candidate_tree: 433ba54cbcdce0e9a61af102b611a3ec10eb4003
independence_status: independent
implementation_reviewed: true
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
release_authorized: false
checks_run_in_documentation_pass: none
supersedes_w4a: reviews/W4A-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
tags: [w4b, canonical-authority, work-close, data-integrity, fail-open, independent-verification, revise]
---

# TASK-AR-654 Canonical Authority Final Independent W4b

## Independent verdict

`REVISE — P0: 0, P1: 3, P2: 0.`

Candidate `c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9`, tree
`433ba54cbcdce0e9a61af102b611a3ec10eb4003`, is not ready for release. A
distinct independent verifier found three fail-open paths in the actual work
closure flow. In each case malformed or redirected authority data should have
blocked closure without mutation, but `work close` accepted it, succeeded, and
performed closure mutation.

These are closure-authority and data-integrity failures, not presentation or
diagnostic defects. The claim must remain active until all three boundaries
are repaired and a fresh independent W4b reports no P0/P1 findings. No release,
integration, publication, deployment, or downstream mutation is authorized.

This report normalizes checks already completed by a distinct verifier. No new
behavioral checks were run in this documentation-only pass. The prior worker
W4a at
`reviews/W4A-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md` is
superseded by this adverse independent evidence and cannot authorize closure.

## P1-1 — Redirected active-claim authority path is accepted

The verifier redirected a path claimed by the active-claim JSON to a different
location. The actual `work close` path accepted that redirected authority,
completed successfully, and allowed state mutation.

Closure authority must be bound to the exact canonical repository object, not
merely to a caller-supplied path that resolves to some existing location.
Acceptance of the redirected path allows claim data to substitute a different
record at the mutation boundary.

Required repair:

1. derive the authoritative claim and work-item locations from canonical
   repository identity rather than trusting paths supplied by claim JSON;
2. require lexical and resolved-path equality with the canonical direct-file
   location, including rejection of aliases, redirections, and substituted
   locations; and
3. prove rejection happens before every close mutation, with an explicit
   non-mutation regression through the actual `work close` command.

## P1-2 — Falsy non-string `unit_spec` values are treated as absent

Active-claim `unit_spec` values `null`, `false`, `0`, `[]`, and `{}` were
treated as though the authority field were absent. For each invalid shape, the
actual `work close` flow succeeded instead of rejecting the claim, and the
expected non-mutation guarantee failed.

An authority-bearing field cannot use truthiness to distinguish omission from
validity. Presence with the wrong JSON type or an empty value is malformed
authority and must fail closed; it must not enter a compatibility fallback or
be silently normalized to “missing.”

Required repair:

1. distinguish a genuinely absent key from a present invalid value;
2. require `unit_spec` to be a non-empty string before path or identity use;
3. reject every other JSON type and blank string before closure assessment or
   mutation; and
4. retain actual-command regressions for `null`, `false`, `0`, `[]`, and `{}`
   with state snapshots proving no mutation.

## P1-3 — Invalid canonical frontmatter identity values are treated as missing

Canonical work-item frontmatter identity fields containing container or blank
values, including `id: []`, were treated as missing rather than malformed.
The actual `work close` flow then succeeded and mutated state, contrary to the
required non-mutation behavior.

Canonical identity is an authority boundary. A present identity key with a
blank, list, mapping, boolean, numeric, or null value cannot be discarded and
reconstructed from the filename. Doing so lets malformed canonical data gain
authority from a secondary inference path.

Required repair:

1. distinguish absent identity keys from present invalid values in the
   frontmatter parser and closure validator;
2. require every authority-bearing identity value to have its canonical
   non-empty scalar-string shape;
3. reject container, blank, null, boolean, and numeric values without filename
   fallback; and
4. verify rejection before mutation through the actual `work close` seam.

## Positive evidence and limits

The verifier also recorded the following passing evidence on the candidate:

| Check | Result |
| --- | --- |
| Existing focused regressions | `10 passed` |
| Compatibility matrix | `25 passed` |

Those passes establish compatibility for their covered valid and previously
known invalid cases. They do not cover or neutralize the three independently
observed fail-open cases above. Because each failing case reached the real
closure command and violated its non-mutation requirement, additional broad
suite success cannot change this W4b verdict.

## Release boundary

The unit remains blocked at W4b. Repair must cover canonical path binding,
strict JSON authority shapes, strict frontmatter identity shapes, and
pre-mutation rejection. A distinct verifier must then repeat the adversarial
actual-close cases, the focused regressions, the compatibility matrix, and
the non-mutation assertions against the repaired candidate.

This documentation-only pass created this report and performed no behavioral
probe, claim release, closure, integration, commit, push, tag, publication,
deployment, or external action.
