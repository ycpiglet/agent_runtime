---
title: TASK-AR-654 Physical-Line Boundary Closeout Skeptic Review
date: 2026-08-01
created_at: 2026-08-01T00:41:04+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: codex-skeptic-task-ar-654-physical-line-closeout
reviewer_role: skeptic
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 3, P2: 1}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
repair_replan_commit: 255d5aa56ac23fed0f110982f5b42d3bfea503d2
failure_first_commit: 8f90916ceddf197e477f0d963f45579800ead1bd
candidate_commit: 0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458
candidate_tree: 5b2d194c38ffbc77fde12432ae32c6bfab0a7e86
w4a: reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
triggering_skeptic: reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
tags: [skeptic, compound, accepted-watch, physical-lines, utf8, stop-hook, claim-authority, revise]
---

# TASK-AR-654 Physical-Line Boundary Closeout Skeptic Review

## Verdict

`REVISE — P0: 0, P1: 3, P2: 1.`

The exact physical-line repair in candidate
`0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458` (tree
`5b2d194c38ffbc77fde12432ae32c6bfab0a7e86`) correctly closes the
previously reported `str.splitlines()` normalization bypass. That narrower
repair is not enough to close TASK-AR-654. Fresh endpoint probes found two
product-level ways for a declared repeated failure to escape the mandatory
Compound Stop decision, plus one current lifecycle state that cannot pass the
ordinary task/unit closeout consumers.

The W4a assertion of zero findings is therefore not independently sustained.
The repair claim must remain held until the P1s are repaired failure-first,
the current-work authority records are made internally consistent, and a new
exact candidate receives fresh evidence and independent review.

## P1 — Malformed UTF-8 turns required-Compound Stop validation into silent approval

`src/agent_runtime/knowledge_records.py:307-308` and the packaged helper read
accepted-watch Markdown as strict UTF-8. The JSON path at lines 376-385 does
the same. However, `_accepted_watch_findings()` at lines 418-421 catches
`OSError`, `JSONDecodeError`, and `CompoundRecordError`, but not
`UnicodeDecodeError`. The decoded-input error therefore escapes the bounded
invalid-watch result.

That exception has different endpoint effects:

| Surface | Fresh result |
| --- | --- |
| source helper, malformed Markdown | raises `UnicodeDecodeError` |
| packaged helper, malformed Markdown | raises `UnicodeDecodeError` |
| source helper, malformed JSON | raises `UnicodeDecodeError` |
| packaged helper, malformed JSON | raises `UnicodeDecodeError` |
| `scripts/work.py close` | exit `1` with traceback; unit bytes remained unchanged |
| direct `closure_gate.repeated_failure_requirement()` | raises `UnicodeDecodeError` |
| actual `scripts/stop_hook_closure_gate.py` | exit `0`, empty stdout, empty stderr |

The Stop result is a fail-open authority bypass, not merely poor diagnostics.
`scripts/stop_hook_closure_gate.py:42-44` intentionally converts every gate
exception into an approval path, and `_emit_stop_payload()` emits nothing for
approval. A byte-invalid review is a valid Git repository object, so a
corrupt or adversarial current-work prevention ref can make the repeated-
failure Stop obligation disappear.

The control probe used the same required current-work Compound and changed
only the watch input from invalid UTF-8 to decoded U+001C FS. The new physical-
line parser converted FS into an ordinary invalid-watch finding, and the
actual Stop wrapper emitted:

```json
{"decision":"block","reason":"repeated-failure-compound-required"}
```

Required repair:

1. Convert malformed UTF-8 for both Markdown and JSON accepted watches into
   the same `compound:prevention-watch-invalid:<ref>` result as other malformed
   authority input. Do not let it escape to the best-effort Stop catch.
2. Add failure-first helper, `work close`, direct closure-gate, and actual
   Stop-wrapper regressions for byte-invalid Markdown and JSON.
3. Keep `work close` non-mutating on failure, but return bounded findings
   rather than a traceback.
4. Couple the repair with the raw-size bound in P2 so decoding and scanning
   cannot be forced into an unbounded failure class.

## P1 — Public claim-only repeated-failure declarations are discarded before Stop evaluation

The claim CLI publicly accepts repeatable `--defect-signature` and
`--escalation-trigger repeated_failure` values and persists them on the claim.
The active repair claim uses that path: it carries both
`repeated_failure` and defect signature
`defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694`.

`scripts/closure_gate.py:193-249` reads the active claim only to resolve its
unit path. It then appends only the parsed unit frontmatter to `contexts` and
discards the claim's `defect_signatures`, `escalation_triggers`, and
`compound_refs`. Explicit `--work-id` mode at lines 188-191 also reads only
the work item. Consequently, a declaration made through the supported claim
interface does not reach `repeated_failure_requirement()`.

A disposable actual-Stop reproduction used:

- one active claim carrying only `repeated_failure` and a normalized defect
  signature;
- its canonical unit with a linked generic review and no Compound; and
- churn below the ordinary substantial-work threshold.

The result was:

```text
repeat_failure.required=false
repeat_failure.defect_signatures=[]
repeat_failure.escalation_triggers=[]
decision=approve
reason=not-substantial
Stop wrapper: exit 0, empty stdout
```

As a control, projecting the exact same trigger and signature into the unit
without adding a Compound changed the decision to
`block / repeated-failure-compound-required`, and the actual Stop wrapper
emitted block JSON. This distinguishes the defect from Compound validation or
the physical-line parser: it is a claim-to-closeout authority aggregation
gap.

The current repair work shows the same inconsistency. At the reviewed state,
the repair claim declares the repeated failure while
`closure_gate.py --work-id UNIT-TASK-AR-654-001` reports
`repeat_failure.required=false` because the unit/task metadata does not carry
that declaration.

Required repair:

1. Define one authoritative propagation rule: either atomically persist claim
   declarations into the canonical task/unit, or merge only the identity-
   matched active claim's repeat fields into closure contexts. Do not infer
   across ambiguous claims.
2. Add claim-CLI-to-actual-Stop regressions for a claim-only signature,
   claim-only `repeated_failure`, linked generic review, and low churn.
3. Repair TASK-AR-654's current task/unit metadata as well; that one-off state
   repair does not replace the product regression.

## P1 — Current Compound and evidence authorities cannot close both unit and task

At reviewed administrative HEAD `650a25364f092feddd6d7e64af44158f8dc72b3c`,
the new current-work Compound record
`COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b`
is internally valid and the canonical store check passes. Its direct
`work_ids`, however, contains only `UNIT-TASK-AR-654-001`.

`scripts/work.py:2528-2537` requires a direct intersection with a record's
`work_ids`; signature equivalence is not sufficient for current-work
authority. A read-only hypothetical task close with that exact record
therefore returned both:

```text
closeout:compound-work-mismatch:TASK-AR-654
closeout:repeat-defect-current-compound-required
```

The unit has a second independent closeout blocker. Its `evidence_refs`
contains two Markdown reviews:

- `reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md`
- `reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md`

`scripts/work.py:2342-2370` JSON-decodes every `evidence_refs` entry. A
read-only exact unit closeout validation rejected both Markdown files with
`closeout:evidence-invalid-json`. The current Compound itself passed the
unit-linked prevention check, so these are evidence-typing failures rather
than a parser false positive.

Required state repair before any release of the claim:

1. The still-unmerged current Compound must directly link both
   `UNIT-TASK-AR-654-001` and `TASK-AR-654`. Because record content is
   digest-addressed, amend the ID, filename, index, and every reference
   together; do not mutate an accepted historical record in place.
2. Keep machine verification JSON only in `evidence_refs`. Move W4a, W4b,
   skeptic, and other human review documents to `review_refs` with valid work
   linkage.
3. Replay both unit and task closeout validation before release/merge/close.

## P2 — Accepted-watch files are read and scanned without a raw-size bound

The Markdown path calls `stream.read()` without a limit at
`knowledge_records.py:307-308`, and the JSON path uses unbounded
`Path.read_text()` at lines 376-380. `MAX_FRONTMATTER_SCALAR` is enforced only
after the complete document has been decoded and scanned. Up to 64 declared
prevention refs may be evaluated.

The new delimiter scan is linear and did not show algorithmic amplification
in normal inputs, but an oversized repository-local review can consume
unbounded memory/time before the authority gate reaches a finding. In the
Stop path, resource exceptions also meet the broad best-effort catch described
in P1. Add a shared raw-byte maximum, read at most `limit + 1`, reject
oversized Markdown and JSON as bounded invalid-watch findings, and cover both
helpers and both consumers.

## Physical-line repair checks that passed

The repaired splitter itself generalized beyond the original marker-only
matrix:

| Check | Fresh result |
| --- | --- |
| registered separator/line-ending selection | `70 passed, 738 deselected` |
| eight separators x ten placements x source/package | `160/160` rejected |
| placements | prefix, opening, every authority boundary, embedded scalar, closing, and body |
| LF and CRLF | accepted in source/package |
| mixed LF/CRLF | accepted in source/package |
| closing delimiter at EOF | accepted for LF and CRLF documents |
| lone CR, CR+CRLF, CRLF+CR, LF+CR, body-only CR | rejected in source/package |
| padded/BOM/NUL/early exact-marker variants | no authority granted |
| source/template helper SHA-256 | identical `30913e6d5ff776124beccb5f736846963882bac20c3da68af982177e3dde5b4e` |

The global separator rejection also catches noncanonical boundaries in the
body, so no later body placement restores authority. Valid JSON formatted
with LF, CRLF, or JSON-permitted lone CR remained accepted. A valid JSON
supplementary field containing escaped U+2028 remained compatible; placing a
noncanonical value in an authority field still fails the existing semantic
checks. This supports the W4a's narrow compatibility claim, subject to the
malformed-byte and size findings above.

The current Compound store passed `scripts/compound_record.py --root . check`.
No historical record deletion or rewrite was observed in the reviewed range;
the lifecycle issue is the still-unmerged current record's incomplete direct
work identity and typed-ref placement.

## Evidence boundary

I inspected the complete implementation range and the repaired source/package
consumers, but did not trust W4a as acceptance evidence. I reran the targeted
70-case registered selection and fresh adversarial probes; I did not rerun the
full suite because the reproducible P1s already require a new candidate.

This report is the sole repository file I changed. I did not change product or
test code, task/unit/claim state, Compound records or indexes, evidence files,
consumer repositories, commits, branches, worktrees, merges, pushes, tags,
packages, deployments, releases, credentials, providers, network state, or
external systems.
