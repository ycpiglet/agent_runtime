---
title: TASK-AR-654 Physical-Line Boundary Repair W4a
date: 2026-08-01
created_at: 2026-08-01T00:31:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: le-20260801-000005-kst-ar654repair001
status: passed
signal: pass
verdict: PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
repair_replan_commit: 255d5aa56ac23fed0f110982f5b42d3bfea503d2
failure_first_commit: 8f90916ceddf197e477f0d963f45579800ead1bd
candidate_commit: 0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458
candidate_tree: 5b2d194c38ffbc77fde12432ae32c6bfab0a7e86
verification_evidence: reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801002151.json
superseded_approval: reviews/W4B-2026-07-31-unit-task-ar-654-001-yaml-conformance-final.md
triggering_skeptic: reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json
tags: [w4a, compound, accepted-watch, physical-lines, unicode, regression]
---

# TASK-AR-654 Physical-Line Boundary Repair W4a

## Verdict

`PASS_PENDING_FRESH_INDEPENDENT_W4B_AND_SKEPTIC — P0: 0, P1: 0, P2: 0.`

Candidate `0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458` closes the P1
physical-line authority bypass found after the prior approval. It preserves
raw newline information, accepts only LF and CRLF, and rejects every
noncanonical separator before any structural split. This is worker
self-verification only. The repair claim remains held until a distinct
independent auditor and a fresh skeptic both approve this exact candidate.

## Exact review target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Repair replan checkpoint | `255d5aa56ac23fed0f110982f5b42d3bfea503d2` |
| Failure-first commit | `8f90916ceddf197e477f0d963f45579800ead1bd` |
| Implementation candidate | `0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458` |
| Candidate tree | `5b2d194c38ffbc77fde12432ae32c6bfab0a7e86` |
| Worker | `le-20260801-000005-kst-ar654repair001` |
| Claim | `CLAIM-20260801-000156-task-ar-654-ar654repair001` |

The candidate changes only the source and packaged accepted-watch reader, its
two registered consumer test files, the intentional mirror digest, and the
derived host lock. The current-work Compound record and this review are
append-only repair evidence outside the implementation candidate.

## RED: preserve the reproduced bypass

The failure-first commit preceded the implementation. On the previous parser,
the exact physical-line selection produced `66 failed, 4 passed, 738
deselected`:

- VT, FF, FS, GS, RS, NEL, U+2028, and U+2029 at both opening and closing
  delimiters failed through the source and packaged helpers: `32/32`;
- the same eight separators failed through `work close`: `16/16`;
- the same eight separators failed through work-linked Stop: `16/16`;
- lone CR failed through both helper copies: `2/2`; and
- the four LF and CRLF positive controls already passed.

This exactly separates the new physical-boundary defect from canonical line
endings and prevents a repair that merely special-cases one reported byte.

## GREEN: raw physical-line contract

Both helper copies now open Markdown with `newline=""`, retaining the original
line endings before parsing. A shared bounded splitter then:

- rejects VT, FF, FS, GS, RS, NEL, U+2028, and U+2029 anywhere in the authority
  document;
- normalizes CRLF to LF;
- rejects every remaining CR as a lone or mixed noncanonical terminator; and
- splits only on LF.

The exact selection now reports `70 passed, 738 deselected`. The two complete
closure-consumer files report `808 passed`, so prior duplicate-key, semantic
key, scalar, indentation, reviewer, ownership, JSON, and compatibility cases
remain green.

## Compatibility, parity, and prevention

Canonical LF and CRLF Markdown remains accepted. Valid JSON behavior is
unchanged because JSON does not use the Markdown frontmatter reader. Exact
column-zero delimiters, ASCII-only YAML separation, non-lossy authority
tokens, canonical work links, and all earlier malformed-input rejections stay
in force.

The source and packaged helpers are byte-identical at SHA-256
`30913e6d5ff776124beccb5f736846963882bac20c3da68af982177e3dde5b4e`.
The template mirror reports 84 expected/common paths, 81 identical paths, 3
intentional differences, and zero findings. The generated host lock is
current; no dependency was added.

The repeated occurrence is recorded under stable defect signature
`defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694` in
`COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b`.
Its prevention destinations are both registered consumer test files. The
scope amendment declares the record and Compound index without widening the
ordinary-work closure contract or rewriting any legacy record.

## Verification

| Verification | Result |
| --- | --- |
| Failure-first physical-line selection | `66 failed, 4 passed, 738 deselected` before repair |
| Exact physical-line selection after repair | `70 passed, 738 deselected` |
| Both closure-consumer files | `808 passed` |
| Fresh registered work-verification suite | `1032 passed` in `50.96s` |
| Full Runtime suite on exact candidate | `3875 passed, 3 skipped, 4 known UI warnings` in `210.62s` |
| Runtime asset usage | pass; 39 assets, 0 block, 0 watch |
| Template mirror | pass; 84 expected/common, 81 identical, 3 intentional, 0 findings |
| Host lock | pass; current |
| Canonical Compound store | pass |
| Security-service active-claim check | pass; 0 findings |
| Active footprint-conflict check | pass; 0 findings |
| `git diff --check` | pass |

Fresh machine evidence
`reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801002151.json` has
SHA-256
`16015c9c7ebb6bb58691aefc89e870aa7708ee264b15c5f2ef1f65596138e893`.
The full-suite warnings are the four pre-existing UI route-sweep invalid-escape
deprecation warnings; no test failed.

## Boundary and next gates

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer-repository, version, tag, package
publication, push, deployment, or release action occurred.

Request a fresh W4b over repair range
`255d5aa56ac23fed0f110982f5b42d3bfea503d2..0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458`
and complete implementation range
`e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458`.
The independent auditor must replay the physical-line matrix and prior
accepted-watch regressions. The skeptic must attempt to generalize beyond the
reported separators and inspect the raw-read boundary, all consumers, JSON
compatibility, and append-only Compound behavior. Only two fresh approvals may
release the repair claim for local integration.
