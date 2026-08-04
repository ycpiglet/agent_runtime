---
title: TASK-AR-654 Duplicate Authority Repair W4a
date: 2026-07-31
created_at: 2026-07-31T05:25:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
reviewer: le-20260731-040735-kst-ar654001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
first_revise_commit: a90a51c8d605fbc95a2d87984d8deabecbbe32dc
second_revise_commit: 3360a637b4c4416caa6dab0c4de9ce9139e6437f
candidate_commit: 84404f2e5e6bef5577410eee488a6c61532e190f
candidate_tree: 6dace9cc19b6a0660a66bf73f169550a3553fa7b
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731052414.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-654-001-accepted-watch-authority-repair.md
first_revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-654-001.md
second_revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-654-001-accepted-watch-authority-repair.md
tags: [w4a, compound, accepted-watch, authority, duplicate-keys, repair, regression]
---

# TASK-AR-654 Duplicate Authority Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `84404f2e5e6bef5577410eee488a6c61532e190f` repairs the
duplicate-key authority bypass found by the second independent W4b. This is
worker self-verification, not acceptance. Both prior independent `REVISE`
reports and both earlier W4a reports remain immutable evidence. The claim
stays active until a fresh, distinct verifier approves this exact candidate.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| First W4b `REVISE` evidence commit | `a90a51c8d605fbc95a2d87984d8deabecbbe32dc` |
| First authority repair | `ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4` |
| Second W4b `REVISE` evidence commit / repair base | `3360a637b4c4416caa6dab0c4de9ce9139e6437f` |
| Duplicate-key repair candidate | `84404f2e5e6bef5577410eee488a6c61532e190f` |
| Candidate tree | `6dace9cc19b6a0660a66bf73f169550a3553fa7b` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Claim | `CLAIM-20260731-040735-task-ar-654-ar654001` |
| Repair footprint | 6 declared paths changed, 0 undeclared |

The repair changes only the authoritative/package Compound helper pair, their
mirror hash and generated host lock, and the two registered test files. It
does not modify a consumer repository, historical Compound record, claim,
release surface, or unrelated lifecycle state.

## RED: Duplicate-Key Authority Was Parser-Order Dependent

The second W4b demonstrated last-value-wins behavior in both accepted-watch
readers. For each of `decision`, `status`, `reviewed_by`, and `work_id`, an
invalid value followed by a valid duplicate closed repeated-failure work
through both actual `work.py close` and the work-linked Stop gate. Reversing
the order blocked only because the invalid value happened to survive.

Before production changes, registered end-to-end tests exercised:

- Markdown and JSON;
- all four authority fields;
- invalid-then-valid and valid-then-invalid order; and
- actual work close and work-linked Stop closure.

All 32 assertions failed first. Sixteen exposed unsafe approvals; the other
sixteen proved that reverse-order blocks were semantic side effects rather
than the required unambiguous duplicate-field rejection.

## GREEN: Duplicate-Aware, Fail-Closed Parsing

JSON accepted-watch documents now use an object-pair hook that rejects a key
on its second occurrence before normalization. Markdown frontmatter now
retains a seen-key set and applies the same rule. Duplicate fields are invalid
regardless of order, value equality, or whether the surviving value would
otherwise be accepted.

The validation boundary remains consumption-time only. Parser errors become
`compound:prevention-watch-invalid:<ref>`, so both mandatory closure
consumers block and require a current-work Compound. Historical append-only
Compound records and legacy logs are not read-modify-written.

After the repair, all 32 end-to-end duplicate cases pass. The earlier 12
reviewer/alias regressions and valid accepted-watch controls remain green.

## Source, Template, and Packaging Boundaries

The authoritative `src/agent_runtime/knowledge_records.py` and standalone
consumer `compound_record.py` template are byte-identical at SHA-256
`5ec29ae67b7ae1855d50ffbe6167b35360ecf11cb889a73b06aa874301a74c0c`.
The intentional wrapper/template mirror contract records that exact template
hash, and the generated host lock is current.

The pre-existing repeated-failure contract is unchanged: ordinary work may
still close with a linked review or retro, while work declaring
`repeated_failure` or a defect signature requires a current-work canonical
Compound with a supported repository-contained prevention destination.

## Verification

| Verification | Result |
| --- | --- |
| Full Runtime suite at the exact candidate tree | `3161 passed, 3 skipped, 4 known UI warnings` in `175.17s` |
| Fresh registered work-verification suite | `318 passed` in `13.37s` |
| Failure-first duplicate-key matrix | `32 failed` before repair |
| Repaired duplicate-key matrix | `32 passed` |
| Runtime asset usage | 39 assets, 713 uses, 0 block, 0 watch |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock current check | pass |
| Authoritative/package Compound helper parity | pass |
| Commit-time owner-governance aggregate | exit 0; pre-existing non-blocking watches only |
| `git diff --check` | pass |

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731052414.json`
has SHA-256
`c85dcecaaecdf02bb0b075ddc795c8b4798c3dcef0081df53842b1b64ef72d54`.
The four full-suite warnings are the existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, release,
or consumer-repository action occurred.

Request a fresh independent W4b over repair range
`3360a637b4c4416caa6dab0c4de9ce9139e6437f..84404f2e5e6bef5577410eee488a6c61532e190f`
and complete
implementation range
`e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..84404f2e5e6bef5577410eee488a6c61532e190f`.
The verifier must independently replay both key orders for all four authority
fields in Markdown and JSON through both closure consumers, then replay the
original empty/null/false/placeholder reviewer and alias-only decision
attacks, valid controls, packaging, claim-time lookup ordering, and
append-only boundaries. Only an independent `APPROVE` permits claim release
and local W5 integration.
