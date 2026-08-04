---
title: TASK-AR-654 YAML Semantic Key Repair W4a
date: 2026-07-31
created_at: 2026-07-31T05:49:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
reviewer: le-20260731-040735-kst-ar654001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
yaml_revise_commit: 954edad7c7231cf09153e363dd76c390e0b05d90
candidate_commit: 85edf874b0ac0efd28bd25f75107c6d1bcf72f0f
candidate_tree: efa0ead933edcc3143cddc336607c4315b8c0828
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json
superseded_w4a: reviews/W4A-2026-07-31-unit-task-ar-654-001-duplicate-authority-repair.md
yaml_revise_w4b: reviews/W4B-2026-07-31-unit-task-ar-654-001-duplicate-authority-repair.md
tags: [w4a, compound, accepted-watch, yaml, semantic-keys, duplicate-keys, repair, regression]
---

# TASK-AR-654 YAML Semantic Key Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B — P0: 0, P1: 0, P2: 0.`

Candidate `85edf874b0ac0efd28bd25f75107c6d1bcf72f0f` repairs the
quoted-versus-plain YAML semantic-key bypass found by the third independent
W4b. This is worker self-verification, not acceptance. All three independent
`REVISE` reports and their preceding W4a reports remain immutable evidence.
The claim remains active until a fresh, distinct verifier approves this exact
candidate.

## Exact Review Target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| YAML-key W4b `REVISE` evidence commit / repair base | `954edad7c7231cf09153e363dd76c390e0b05d90` |
| Repair-base tree | `857ba4eab1c202db8fd656b5b42c51a6ddfa5697` |
| YAML semantic-key repair candidate | `85edf874b0ac0efd28bd25f75107c6d1bcf72f0f` |
| Candidate tree | `efa0ead933edcc3143cddc336607c4315b8c0828` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Claim | `CLAIM-20260731-040735-task-ar-654-ar654001` |
| Repair footprint | 6 declared paths changed, 0 undeclared |

The repair changes only the authoritative/package Compound helper pair, their
mirror hash and generated host lock, and the two registered test files. It
does not modify a consumer repository, historical Compound record, claim,
release surface, or unrelated lifecycle state.

## RED: Raw Spelling Diverged from YAML Key Identity

The third W4b proved that the lightweight Markdown reader treated
`"decision"` and `decision` as different raw keys even though YAML assigns
both the semantic key `decision`. With the conflicting value on the quoted
occurrence and the acceptable value on the plain occurrence, actual
`work.py close` exited zero and the work-linked Stop gate approved the same
current-work Compound.

Before production changes, registered end-to-end tests covered:

- `decision` and `status`;
- all five reviewer authority fields;
- `work_id`, `task_id`, `unit_id`, and `work_ids`;
- plain versus single-quoted, double-quoted, and escaped double-quoted keys;
- quoted-first and plain-first order;
- conflicting values in either spelling and equal-value duplicates;
- unique quoted-key positive controls; and
- both actual work close and work-linked Stop closure.

All 336 assertions failed first. Some exposed unsafe approvals; the remaining
cases proved that semantic duplicates were blocked only for unrelated value
reasons rather than the required duplicate-key invalidation, or that a unique
valid quoted key was not recognized.

## GREEN: Bounded Semantic Key Contract

Markdown accepted-watch keys now enter one bounded representation before
duplicate detection:

- plain keys must match the portable scalar-key grammar;
- single-quoted keys are decoded with YAML doubled-quote semantics;
- double-quoted keys are decoded with the standard-library JSON-compatible
  escape subset; and
- unsupported complex, tagged, merge, explicit-key, malformed, or
  non-portable syntax invalidates the accepted-watch document instead of
  being ignored.

The normalized key is then checked against `seen`, so quoted/plain, escaped,
equal-value, conflicting, and either-order duplicates all fail closed.
Unique supported quoted keys retain normal accepted-watch behavior. JSON
continues to use duplicate-aware object-pair parsing.

The repair deliberately avoids a new YAML dependency in the standalone
consumer script. Its supported syntax is explicit and fail-closed rather than
claiming to implement the full YAML type system.

After the repair, the 336 semantic-key tests pass. Ten additional end-to-end
cases prove that explicit keys, tags, merge keys, unsupported escapes, and
unclosed quoted keys are invalid through both consumers. The earlier exact
duplicate, reviewer scalar, alias-only decision, valid watch, and ordinary
closure controls remain green.

## Source, Template, and Append-Only Boundaries

The authoritative `src/agent_runtime/knowledge_records.py` and standalone
consumer `compound_record.py` template are byte-identical at SHA-256
`3ec98ecb3c238ae663a72f097269accebfb2244155be6e22413c0f30da71da1c`.
The intentional wrapper/template mirror contract records that exact hash, and
the generated host lock is current.

Validation remains consumption-time only. Parser failures become
`compound:prevention-watch-invalid:<ref>`, causing both repeated-failure
closure consumers to require a valid current-work Compound. Historical
append-only Compound records and legacy logs are not rewritten or
bulk-invalidated.

## Verification

| Verification | Result |
| --- | --- |
| Full Runtime suite at the exact candidate tree | `3507 passed, 3 skipped, 4 known UI warnings` in `199.06s` |
| Fresh registered work-verification suite | `664 passed` in `32.81s` |
| Failure-first YAML semantic-key matrix | `336 failed` before repair |
| Repaired YAML semantic-key matrix | `336 passed` |
| Unsupported-key-syntax end-to-end additions | `10 passed` |
| Related authority regression slice | `358 passed` |
| Runtime asset usage | 39 assets, 713 uses, 0 block, 0 watch |
| Template mirror gate | 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock and canonical Compound store | pass |
| Authoritative/package Compound helper parity | pass |
| Commit-time owner-governance aggregate | exit 0; pre-existing non-blocking watches only |
| `git diff --check` | pass |

Fresh machine evidence
`reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json`
has SHA-256
`d25cbb6b5a83cfa5bc05a0b510a0ef7333cd18dae657d0166c14ceacc78409b2`.
The four full-suite warnings are the existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Boundary and Next Gate

No credential, provider, live network, broker, order, database migration,
notification, version, tag, package publication, push, deployment, release,
or consumer-repository action occurred.

Request a fresh independent W4b over repair range
`954edad7c7231cf09153e363dd76c390e0b05d90..85edf874b0ac0efd28bd25f75107c6d1bcf72f0f`
and complete implementation range
`e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..85edf874b0ac0efd28bd25f75107c6d1bcf72f0f`.
The verifier must independently replay quoted/plain and escaped semantic
duplicates for every authority family, both orders and consumers, equal-value
duplicates, unique quoted controls, unsupported syntax, the two earlier W4b
families, packaging, claim-time lookup ordering, deterministic search, and
append-only boundaries. Only an independent `APPROVE` permits claim release
and local W5 integration.
