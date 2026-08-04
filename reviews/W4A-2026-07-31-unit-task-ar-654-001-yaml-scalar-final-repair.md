---
title: TASK-AR-654 YAML Scalar Final Repair W4a
date: 2026-07-31
created_at: 2026-07-31T06:14:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
reviewer: le-20260731-040735-kst-ar654001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
scalar_revise_commit: 66d20085e63ffdee7a7d222190cd88ac97876225
candidate_commit: 37d029a815237c5e3930dfcc16352940bbebe9ba
candidate_tree: 20cdb204380ab785b0244d33470895d79862bfbe
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731061244.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-654-001-yaml-semantic-key-repair.md
scalar_revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-654-001-yaml-semantic-key-final.md
tags: [w4a, compound, accepted-watch, yaml, scalar-values, indentation, repair, regression]
---

# TASK-AR-654 YAML Scalar Final Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `37d029a815237c5e3930dfcc16352940bbebe9ba` repairs the YAML
scalar-value and unexpected-indentation bypass found by the fourth independent
W4b. This is worker self-verification, not acceptance. All four independent
`REVISE` reports and the preceding W4a reports remain immutable evidence. The
claim stays active until a fresh, distinct verifier approves this exact
candidate.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Scalar W4b `REVISE` evidence commit / repair base | `66d20085e63ffdee7a7d222190cd88ac97876225` |
| Repair-base tree | `7a64c1cdef06be15c004266aac93596c97266563` |
| Scalar/indent repair candidate | `37d029a815237c5e3930dfcc16352940bbebe9ba` |
| Candidate tree | `20cdb204380ab785b0244d33470895d79862bfbe` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Claim | `CLAIM-20260731-040735-task-ar-654-ar654001` |
| Repair footprint | 6 declared paths changed, 0 undeclared |

The repair changes only the authoritative/package Compound helper pair, their
mirror hash and generated host lock, and the two registered test files. It
does not modify a consumer repository, historical Compound record, claim,
release surface, or unrelated lifecycle state.

## RED: Quote Characters Were Trimmed, Not Decoded

The fourth W4b proved that `str.strip("\"'")` repeatedly removed either quote
character from both ends of Markdown values and list items. Valid YAML scalars
whose semantic value retained inner quotes and malformed mixed-quote values
therefore collapsed into exact accepted authority. Non-list indented content
was also silently discarded.

Before production changes, end-to-end tests covered all 11 authority fields:

- `decision` and `status`;
- all five reviewer fields;
- `work_id`, `task_id`, `unit_id`, and `work_ids`;
- nested paired single/double quote forms;
- both mixed/unclosed quote directions;
- proper single/double and Unicode-escaped double-quoted controls; and
- space-indented, tab-indented, malformed continuation, and orphan-list
  content.

The failure-first result was `118 failed, 44 passed`. The failures comprised
88 unsafe nested/malformed authority approvals, 22 rejected but semantically
valid Unicode-escape controls, and eight silently accepted indentation cases.
The 44 already-passing controls were properly paired single/double values.

## GREEN: One Bounded Scalar Decoder

Top-level values and list items now share one standard-library-only decoder:

- surrounding YAML separation whitespace is removed once;
- plain scalar text is otherwise preserved;
- single-quoted values require one matching pair and decode only doubled
  single quotes;
- double-quoted values require one matching pair and use the JSON-compatible
  escape subset;
- malformed or mixed quotes, unsupported syntax, oversized values, and
  decoded control characters invalidate the watch; and
- decoded nested quotes remain part of the semantic value and therefore
  cannot satisfy exact decision, status, reviewer, or work-link authority.

Nonblank, noncomment indented content is accepted only as a list item for the
currently active list. Unexpected indentation no longer disappears from the
authority document.

After repair, all 162 new scalar/indent tests pass. Proper single/double and
Unicode-escaped authority values close successfully; nested semantic values
block without being rewritten; malformed values and unsupported indentation
produce `compound:prevention-watch-invalid`.

## Prior Families and Boundaries

The preceding semantic-key matrix, exact Markdown/JSON duplicate matrix,
reviewer placeholder and alias-only decision cases, valid watch controls,
ordinary review/retro compatibility, parent repeated-failure aggregation,
prevention containment, current-work ownership, claim lookup ordering,
deterministic Compound search/index behavior, and append-only boundaries
remain green.

The authoritative `src/agent_runtime/knowledge_records.py` and standalone
consumer `compound_record.py` template are byte-identical at SHA-256
`780b07a6b83ec343f4a37b28fe2a63ff7da112233ce8f540d1677483cabd8e11`.
The intentional mirror contract records that exact hash and the generated
host lock is current. No new YAML dependency was introduced.

## Verification

| Verification | Result |
| --- | --- |
| Full Runtime suite at the exact candidate tree | `3669 passed, 3 skipped, 4 known UI warnings` in `208.09s` |
| Fresh registered work-verification suite | `826 passed` in `42.64s` |
| Failure-first scalar/indent matrix | `118 failed, 44 passed` before repair |
| Repaired scalar/indent matrix | `162 passed` |
| Runtime asset usage | 39 assets, 713 uses, 0 block, 0 watch |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock and canonical Compound store | pass |
| Authoritative/package Compound helper parity | pass |
| Commit-time owner-governance aggregate | exit 0; pre-existing non-blocking watches only |
| `git diff --check` | pass |

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731061244.json`
has SHA-256
`dfda446fa31330af76b5e0fbe62f0b09fc527c08a08a608df7b397b5847d4c71`.
The four full-suite warnings are the existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, release,
or consumer-repository action occurred.

Request a fresh independent W4b over repair range
`66d20085e63ffdee7a7d222190cd88ac97876225..37d029a815237c5e3930dfcc16352940bbebe9ba`
and complete implementation range
`e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..37d029a815237c5e3930dfcc16352940bbebe9ba`.
The verifier must independently replay all scalar and indentation cases,
proper paired and escaped controls, all preceding W4b families, packaging,
claim-time lookup, deterministic search, and append-only boundaries. Only an
independent `APPROVE` permits claim release and local W5 integration.
