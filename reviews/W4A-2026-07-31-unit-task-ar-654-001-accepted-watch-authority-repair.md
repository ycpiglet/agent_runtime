---
title: TASK-AR-654 Accepted-Watch Authority Repair W4a
date: 2026-07-31
created_at: 2026-07-31T05:00:59+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
reviewer: le-20260731-040735-kst-ar654001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
revise_evidence_commit: a90a51c8d605fbc95a2d87984d8deabecbbe32dc
candidate_commit: ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4
candidate_tree: 85f60fd7415323211513dafd44ad63569c86802c
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731050030.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-654-001.md
revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-654-001.md
tags: [w4a, compound, accepted-watch, authority, repair, regression]
---

# TASK-AR-654 Accepted-Watch Authority Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4`
repairs the P1 accepted-watch authority bypass found by the first independent
W4b. This is worker self-verification, not acceptance. The prior W4a and
independent `REVISE` remain immutable evidence, and the claim remains active
until a distinct verifier approves this exact repair.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Committed W4b `REVISE` evidence | `a90a51c8d605fbc95a2d87984d8deabecbbe32dc` |
| Repaired implementation | `ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4` |
| Repaired tree | `85f60fd7415323211513dafd44ad63569c86802c` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Claim | `CLAIM-20260731-040735-task-ar-654-ar654001` |
| Repair footprint | 6 declared paths changed, 0 undeclared |

The repair changes the authoritative/package Compound helper pair, their
mirror hash and host lock, and the two already registered test files. No
consumer repository, historical Compound record, or unrelated lifecycle
surface changed.

## RED: Independently Reproduced Authority Bypass

The committed W4b proved that these accepted-watch fragments satisfied both
mandatory closure paths without a reviewer:

```yaml
decision: accepted_watch
reviewed_by: []
```

```yaml
decision: accepted_watch
reviewed_by: null
```

It also showed that alias-only `disposition: accepted_watch` and
`prevention_status: accepted_watch` were accepted despite the T3 contract and
consumer skill requiring the explicit `decision` field.

The repair added end-to-end negatives before production changes. All 12 cases
failed first: six through the actual `work.py close` CLI and six through the
work-linked Stop closure gate.

## GREEN: Exact Decision and Scalar Reviewer Identity

An accepted-watch prevention now requires:

- a string-valued `decision` whose normalized value is exactly
  `accepted_watch`;
- accepted or approved status;
- current task/unit linkage; and
- at least one reviewer field containing a bounded agent-style scalar
  identity.

Reviewer values must begin with an ASCII letter, stay within 160 characters,
and use only the Runtime identity character set. Nulls, booleans, numbers,
collections, surrounding whitespace, control/punctuation forms, and explicit
placeholder spellings such as `TBD`, `unknown`, `none`, and `n/a` do not count
as reviewer identity.

`disposition` and `prevention_status` remain ordinary metadata but no longer
substitute for `decision: accepted_watch`.

After the repair, the same 12 end-to-end cases pass by proving both closure
paths block. Valid accepted watches, all other supported prevention kinds,
parent aggregation, ordinary review/retro compatibility, and the explicit
Stop disable escape remain green.

## Source, Template, and Append-Only Boundaries

The authoritative
`src/agent_runtime/knowledge_records.py` and standalone consumer
`scripts/compound_record.py` template are byte-identical at SHA-256
`1e240dfc5c58c88aa8b412c7652a0bb862f0a282b1bff4a192a60211f24feefa`.
The intentional wrapper/template mirror contract and generated host lock were
updated from that exact content.

Validation still occurs only when a Compound is consumed for repeated-failure
closure. Historical store validation and append-only records are not rewritten
or bulk-invalidated.

## Verification

| Verification | Result |
| --- | --- |
| Full Runtime suite at the exact repair tree | `3129 passed, 3 skipped, 4 known UI warnings` in `174.38s` |
| Fresh registered work-verification suite | `286 passed` in `11.54s` |
| Failure-first accepted-watch matrix | `12 failed` before repair |
| Repaired accepted-watch matrix | `12 passed` |
| Valid accepted-watch and compatibility slice | `6 passed` |
| Runtime asset usage | 39 assets, 713 uses, 0 block, 0 watch |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock current check | pass |
| Authoritative/package Compound helper parity | pass |
| `git diff --check` | pass |

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731050030.json`
has SHA-256
`60765e91455b4f5af6c6f8f5bc6cd5a0da00fb3f97911d25d7517e869141c818`.
The full-suite warnings are the existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, release,
or consumer-repository action occurred.

Request a fresh independent W4b over repair range
`a90a51c8d605fbc95a2d87984d8deabecbbe32dc..ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4`
and complete implementation range
`e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4`.
The verifier must independently replay the original empty/null reviewer and
alias-only decision attacks, then recheck valid watches, both closure paths,
packaging, and unchanged claim-time lookup ordering. Only an independent
`APPROVE` permits claim release and local W5 integration.
