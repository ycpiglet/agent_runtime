---
title: TASK-AR-654 YAML Semantic-Key Final Independent W4b
date: 2026-07-31
created_at: 2026-07-31T05:59:00+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
reviewer: codex-independent-task-ar-654-yaml-semantic-key-final-w4b
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
yaml_revise_commit: 954edad7c7231cf09153e363dd76c390e0b05d90
candidate_commit: 85edf874b0ac0efd28bd25f75107c6d1bcf72f0f
candidate_tree: efa0ead933edcc3143cddc336607c4315b8c0828
w4a_admin_head: 6a1c5f2c43849a71965f7e00d27f9b41accb1eaf
w4a_admin_tree: ab6ad4fccd74f09ee4bde13b212d52a9b36ac9d5
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json
tags: [w4b, independent-verification, compound, accepted-watch, yaml, scalar-values, revise]
---

# TASK-AR-654 YAML Semantic-Key Final Independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Candidate `85edf874b0ac0efd28bd25f75107c6d1bcf72f0f` closes the
plain-versus-quoted YAML **key** bypass and preserves the preceding duplicate,
reviewer, alias, ownership, packaging, and append-only controls. It does not
fail closed on YAML **scalar values**. The Markdown reader removes any run of
single or double quote characters from both ends of every scalar and list
item. As a result, a scalar with a different YAML value, or a malformed YAML
scalar that has no value at all, is converted into the exact accepted
authority value.

This was reproduced for `decision`, `status`, all five reviewer fields, and
all four work-link fields through both mandatory closure consumers. It is a
P1 accepted-watch authority bypass. The claim must remain active; this report
does not authorize claim release or W5.

## Exact Review Target and Independence

| Identity | Value |
| --- | --- |
| Complete implementation base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Committed YAML-key W4b `REVISE` / repair base | `954edad7c7231cf09153e363dd76c390e0b05d90` |
| Repaired implementation candidate | `85edf874b0ac0efd28bd25f75107c6d1bcf72f0f` |
| Candidate tree | `efa0ead933edcc3143cddc336607c4315b8c0828` |
| W4a administrative HEAD | `6a1c5f2c43849a71965f7e00d27f9b41accb1eaf` |
| W4a administrative tree | `ab6ad4fccd74f09ee4bde13b212d52a9b36ac9d5` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Independent verifier | `codex-independent-task-ar-654-yaml-semantic-key-final-w4b` |

The candidate-to-W4a administrative range changes only the unit record,
`reviews/INDEX.md`, the fresh machine evidence, and the W4a report. It does
not change implementation or tests. The complete implementation range has
10 commits and 28 changed paths; the final YAML-key repair itself changes the
six declared parser, test, mirror, and lock paths.

I am a fresh agent instance, distinct from the worker and every preceding
W4b verifier. I independently inspected the implementation before using the
earlier reports to preserve their attack families. I made no claim, lock,
index, registry, code, test, lifecycle, consumer, release, or external-system
change. This report is my only repository write.

## P1 — Markdown Scalar Quotes Are Stripped, Not Decoded

The key repair correctly canonicalizes bounded plain, single-quoted,
double-quoted, and escaped double-quoted key spellings before duplicate
detection. The value path remains:

```python
value = value.strip().strip("\"'")
```

and list items use the same quote-character stripping operation. Python
`str.strip(chars)` does not remove one balanced outer quoting pair and decode
that pair. It repeatedly removes either quote character from both ends.
Therefore:

- `decision: "'accepted_watch'"` is YAML scalar `'accepted_watch'`, including
  the single-quote characters, but Runtime converts it to `accepted_watch`;
- `decision: '"accepted_watch"'` is YAML scalar `"accepted_watch"`, including
  the double-quote characters, but Runtime converts it to `accepted_watch`;
- `decision: 'accepted_watch"` and `decision: "accepted_watch'` are malformed
  YAML, but Runtime converts each to `accepted_watch`;
- the same transformation turns nested or malformed `accepted`, reviewer
  identities, and current work IDs into valid authority; and
- the list-item path does the same for `work_ids`.

The defect is not limited to the `reviewed_by` spelling. My independent
matrix covered:

- `decision` and `status`;
- `reviewed_by`, `reviewer`, `approved_by`, `accepted_by`, and `verified_by`;
- `work_id`, `task_id`, `unit_id`, and `work_ids`;
- properly paired single and double quotes;
- paired nested quotes with each outer quote style;
- each mixed/unclosed quote direction; and
- a double-quoted Unicode-escape compatibility probe.

For each document, the probe compared standard YAML semantics and exercised
actual `scripts/work.py close` plus work-linked `closure_gate.assess`.

| Scalar matrix result | Documents | Endpoint checks | Result |
| --- | ---: | ---: | --- |
| Proper paired single/double controls | 22 | 44 | 44 approve |
| Nested paired scalars whose YAML value retains inner quotes | 22 | 44 | **44 unsafe approve** |
| Malformed mixed/unclosed scalars rejected by YAML | 22 | 44 | **44 unsafe approve** |
| Semantically equivalent escaped double-quoted probe | 11 | 22 | 22 fail closed |
| **Total** | **77** | **154** | **88 unsafe approvals** |

Every one of the 11 authority fields produced four unsafe approvals per
consumer family, for eight unsafe endpoint approvals per field. The escaped
probe is not graded separately because the documented watch example does not
promise escaped value syntax; it nevertheless confirms that the routine is
character trimming rather than a coherent bounded decoder.

The same permissive branch silently ignores any indented line that is not a
recognized list item. Four additional documents used a space- or tab-indented
authority line or malformed continuation. Standard YAML either rejected the
document or changed the current-work scalar, while Runtime approved all eight
consumer endpoints.

In total, the independent value/indent probes produced **96 unsafe approvals
across 96 affected endpoint checks**. A malformed or semantically different
review document can therefore substitute for the explicit accepted-watch
authority required to close repeated-failure work.

### Required Repair

1. Replace quote-character stripping with one bounded scalar decoder shared
   by top-level values and list items.
2. Preserve plain scalar text exactly after allowed surrounding whitespace.
3. For a supported single-quoted scalar, require one closing quote and decode
   only YAML doubled-single-quote semantics; reject trailing syntax.
4. For a supported double-quoted scalar, require one closing quote and use a
   bounded decoder such as the already-used JSON-compatible escape subset;
   reject trailing, malformed, nested-as-authority, or unsupported syntax.
5. Reject nonblank, noncomment indented content unless it is a valid list item
   for the currently active list. Do not silently discard it.
6. Add failure-first end-to-end tests for every authority family, both
   consumers, paired nested quotes, both malformed quote directions, and
   unexpected indentation. Include normal plain and properly paired quoted
   controls.
7. Preserve exact authoritative/template parity, regenerate the mirror hash
   and host lock, rerun the full suite, and request a new distinct W4b.

## Closed Attack Families

The current candidate did close the specifically requested key and earlier
authority families:

| Conformance family | Result |
| --- | --- |
| Semantic YAML key duplicates: 11 fields × 3 quoted spellings × both orders × invalid value on either spelling, plus equal values, through both consumers | `330 passed` |
| Unique supported single/double/escaped quoted keys through both consumers | `6 passed` |
| Exact raw Markdown/JSON duplicate keys, four authority categories, both orders, both consumers | `32 passed` |
| Empty-list/null/false/TBD reviewer and alias-only decision attacks through both consumers | `12 passed` |
| Explicit key, tagged key, merge key, unsupported key escape, and unclosed quoted key through both consumers | `10 passed` |
| Valid Markdown and JSON accepted-watch controls | `4/4 endpoint approvals` |

The combined registered authority slice was `390 passed, 50 deselected`.
Separately replayed registered slices were `336 passed` for semantic-key and
unique-key cases, `32 passed` for raw duplicates, and `22 passed` for the
original authority plus malformed-key cases.

## Repeated-Failure, Store, and Compatibility Rechecks

A bounded 27-test cross-seam slice passed for:

- ordinary linked-review closeout and ordinary review/retro compatibility;
- review-only repeated-failure blocking;
- parent repeated-failure inheritance and parent Compound satisfaction;
- regression, executable gate, prevention task, and valid accepted-watch
  destinations;
- missing, unsupported, and symlink-escape prevention refs;
- current-work ownership and unrelated current-work rejection;
- deterministic Compound creation, lookup, search, and index rebuild;
- immutable content-digest enforcement, concurrent append-only record
  creation, and read-only legacy fallback; and
- Compound lookup surfacing before claim persistence, including malformed
  store refusal before a claim artifact is written.

The registered work-verification suite passed:

```text
664 passed in 33.09s
```

Runtime asset usage passed with 39 assets, 713 uses, zero block, and zero
watch findings. Template mirror passed with 84 expected/common paths, 81
identical, three intentional, and zero findings. The host lock is current.
The canonical Compound store check passed. Authoritative
`knowledge_records.py` and standalone template `compound_record.py` are
byte-identical at:

```text
3ec98ecb3c238ae663a72f097269accebfb2244155be6e22413c0f30da71da1c
```

`git diff --check` passed for the complete candidate range. The aggregate
owner-governance command exited zero; its lifecycle/state/release-cadence
watches are nonblocking repository baseline observations and do not change
this parser verdict.

## W4a Evidence Reliance

I verified that the machine evidence file
`reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json` has
SHA-256
`d25cbb6b5a83cfa5bc05a0b510a0ef7333cd18dae657d0166c14ceacc78409b2`
and points to the exact candidate. After checking the candidate commit/tree
and the docs/evidence-only administrative range, I rely on its exact-candidate
full-suite result:

```text
3507 passed, 3 skipped, 4 known UI warnings in 199.06s
```

That broad green suite does not mitigate the independently reproduced P1,
because the unsafe scalar forms were not in the registered regression set.

## Boundary

No credential, provider, network, broker, order, database migration,
notification, consumer repository, version, tag, package publication, push,
deployment, or release action occurred.

Because P1 is nonzero, `REVISE` means:

- keep `CLAIM-20260731-040735-task-ar-654-ar654001` active;
- do not release the claim;
- do not enter local W5;
- repair and replay the scalar/indent matrix; and
- obtain a fresh independent W4b over the new exact candidate.

Even a future `APPROVE` for this unit would permit only claim release and
local W5 integration. It would never authorize an external version, tag,
push, publication, deployment, or release.
