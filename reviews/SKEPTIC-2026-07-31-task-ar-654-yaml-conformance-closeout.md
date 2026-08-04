---
title: TASK-AR-654 YAML Conformance Closeout Skeptic Review
date: 2026-07-31
created_at: 2026-07-31T23:54:53+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
overlay_claim_id: CLAIM-REVIEW-TASK-AR-654-skeptic-closeout
reviewer: codex-skeptic-task-ar-654-closeout
reviewer_role: skeptic
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
candidate_commit: debe338007d417c8b6d0448a0cbec37f3ae0240a
candidate_tree: 08ce4e4acd14b4256a7b35ed3b5a291cfa589e2d
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731233354.json
evidence_sha256: 444c550f92dac20a85e96e38a4eed62069ae779a150cb0228d87746ea0eb8f7f
tags: [skeptic, compound, accepted-watch, yaml, delimiter, control-character, revise]
---

# TASK-AR-654 YAML Conformance Closeout Skeptic Review

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Skeptic reviewer `codex-skeptic-task-ar-654-closeout`, role `skeptic`,
reviewed exact implementation candidate
`debe338007d417c8b6d0448a0cbec37f3ae0240a` (tree
`08ce4e4acd14b4256a7b35ed3b5a291cfa589e2d`) and found one reproducible
P1 authority bypass. The final parser checks delimiter text after Python has
already erased several noncanonical control separators with `str.splitlines()`.
A Markdown prevention watch whose serialized marker is not an exact
column-zero `---` line therefore satisfies both mandatory repeated-failure
closure consumers.

The prior independent `APPROVE` cannot release the implementation claim while
this P1 remains.

## P1 — Control separators are normalized into exact frontmatter delimiters

Candidate `src/agent_runtime/knowledge_records.py:279-290` reads the complete
text, immediately calls `text.splitlines()`, and only then compares the first
and closing logical lines with `---`. Python treats all of the following as
line boundaries and removes them from the resulting strings:

- U+000B VT, U+000C FF;
- U+001C FS, U+001D GS, U+001E RS;
- U+0085 NEL; and
- U+2028 LINE SEPARATOR and U+2029 PARAGRAPH SEPARATOR.

Consequently, a literal C0 control in this serialized opening sequence is
accepted as though a canonical line ending followed the marker:

```text
---<U+001C>status: accepted
decision: accepted_watch
reviewed_by: qa-independent
work_id: UNIT-TASK-AR-645-001
---
```

The inverse also occurs at the closing boundary, for example a literal U+2028
immediately after `---`. This contradicts the candidate's stated bounded
contract that delimiters are exact and that non-ASCII whitespace/control input
does not gain authority. At minimum VT, FF, FS, GS, and RS are C0 controls, not
canonical Markdown/YAML line endings; they are discarded before validation.

### Reproduction results

An in-memory matrix called `_accepted_watch_findings()` against both exact
candidate helper copies. It exercised all eight separators at both opening and
closing marker positions:

| Surface | Result |
| --- | --- |
| `src/agent_runtime/knowledge_records.py` | `16/16` noncanonical watches accepted |
| packaged `scripts/compound_record.py` template | `16/16` noncanonical watches accepted |
| Combined helper matrix | `32/32` unsafe approvals |

Two representative documents were then exercised through the actual closure
consumers in disposable repositories:

| Document | `scripts/work.py close` | work-linked Stop gate |
| --- | --- | --- |
| U+001C FS after opening marker | exit `0`, status `closed` | `approve`, `repeated-failure-compound-present`, satisfied `true` |
| U+2028 after closing marker | exit `0`, status `closed` | `approve`, `repeated-failure-compound-present`, satisfied `true` |

That is `4/4` unsafe endpoint approvals. The Compound exists, but its mandatory
prevention destination is not conformant to the exact-delimiter trust
boundary; accepting it bypasses the prevention-authority requirement.

### Required repair

1. Define and enforce the accepted physical line-ending set before splitting
   authority-bearing Markdown. Do not use Unicode-wide `str.splitlines()` as a
   normalizer at this trust boundary.
2. Reject VT, FF, FS, GS, RS, NEL, U+2028, and U+2029 rather than converting
   them into structural lines. Preserve deliberate LF and CRLF compatibility;
   decide and test lone CR explicitly.
3. Add failure-first opening- and closing-marker regressions for every rejected
   separator through both `work close` and the work-linked Stop gate, plus the
   authoritative and packaged helper parity check.
4. Retain canonical LF/CRLF Markdown and valid JSON controls, all prior
   reviewer/duplicate/key/scalar/indentation/NBSP regressions, mirror digest,
   host lock, and full-suite verification, then request a fresh independent
   W4b on the repaired candidate.

## Why the 136 new regressions do not generalize the five revisions

The registered 96-case repair matrix covers NBSP placement across eleven
authority fields and four malformed list-indentation layouts. The additional
40 controls cover tab/NBSP marker padding and ASCII-padding/fullwidth-NFKC
authority values in Markdown and JSON. The four marker styles are only
`tab-open`, `tab-close`, `nbsp-open`, and `nbsp-close`; none places a control
separator at the physical line boundary.

The suite therefore preserves the earlier reviewer-value, exact-duplicate,
semantic-key, scalar-quote/unexpected-indentation, and NBSP/list-indentation
repairs, but it does not test the lower-level line-splitting normalization on
which all Markdown cases depend. Valid JSON remains covered, yet the Markdown
path can still grant the same authority from a noncanonical serialization.

## Identity, evidence, and completed checks

| Check | Result |
| --- | --- |
| Candidate commit/tree | exact match |
| Complete review range | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..debe338007d417c8b6d0448a0cbec37f3ae0240a` inspected |
| W4a | `reviews/W4A-2026-07-31-unit-task-ar-654-001-yaml-conformance-repair.md` inspected |
| Final independent W4b | `reviews/W4B-2026-07-31-unit-task-ar-654-001-yaml-conformance-final.md` inspected |
| Machine evidence | SHA-256 `444c550f92dac20a85e96e38a4eed62069ae779a150cb0228d87746ea0eb8f7f`, status/signal passed/pass |
| Source/template helper digest | byte-identical SHA-256 `826617de44ebc82cef26ae5e66dfd7b15aef6f08ad201185648d0769129d0187` |
| Compact separator matrix | `32/32` unsafe helper approvals |
| Representative consumer replay | `4/4` unsafe endpoint approvals |
| Registered focus/full evidence | relied on `962 passed` and `3805 passed, 3 skipped, 4 known warnings`; not rerun |
| Finding counts | P0 `0`, P1 `1`, P2 `0` |

## Boundary

This report is the sole repository file I changed. I did not change
implementation, tests, claims, unit/task state, indexes, lifecycle records,
Compound history, package or mirror state, consumer repositories, commits,
branches, worktrees, merges, pushes, releases, network state, credentials,
providers, or external systems.
