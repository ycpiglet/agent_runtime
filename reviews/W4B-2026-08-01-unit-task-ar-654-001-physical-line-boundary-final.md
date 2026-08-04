---
title: TASK-AR-654 Physical-Line Boundary Final W4b
date: 2026-08-01
created_at: 2026-08-01T00:40:09+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
reviewer: ia-20260801-004009-kst-ar654physw4b
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 4, P2: 0}
reviewed_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
failure_first_commit: 8f90916ceddf197e477f0d963f45579800ead1bd
candidate_commit: 0ac8e5071086a3c14fdd91a9a15a8b5b4cd93458
candidate_tree: 5b2d194c38ffbc77fde12432ae32c6bfab0a7e86
w4a_evidence: reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
verification_evidence: reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801002151.json
tags: [w4b, independent-audit, revise, compound, accepted-watch, physical-lines]
---

# TASK-AR-654 Physical-Line Boundary Final W4b

## Verdict and findings first

`REVISE — P0: 0, P1: 4, P2: 0.`

Do not use this report to release
`CLAIM-20260801-000156-task-ar-654-ar654repair001`. The exact physical-line
matrix is green, but the candidate tree still has two independent fail-closed
defects. Two additional closeout-integrity defects in the current W4 evidence
state also prevent a releasable and closable handoff.

### P1-01 — malformed UTF-8 turns Stop validation into silent approval

`_simple_frontmatter_payload()` now correctly opens Markdown with
`newline=""`, but decoding still uses strict UTF-8. `_accepted_watch_findings()`
catches `OSError`, `json.JSONDecodeError`, and `CompoundRecordError`; it does
not catch `UnicodeDecodeError`. The exception therefore escapes the bounded
invalid-watch result.

Independent temporary-root reproduction used a current-work Compound whose
accepted-watch Markdown contained valid authority frontmatter followed by byte
`0xff`:

- `validate_prevention_destinations(...)` raised `UnicodeDecodeError` instead
  of returning `compound:prevention-watch-invalid:<ref>`;
- `python scripts/work.py --root <temp> close <unit> ...` exited `1` with an
  uncaught traceback through `work.py:2538` and
  `knowledge_records.py:308`; and
- the same error under `stop_hook_closure_gate.main([])` returned `0` and
  emitted no output, because its broad best-effort exception branch translates
  every gate error into a silent approve path.

An unreadable authority document must be an ordinary invalid-watch finding,
not a gate exception. Catch the decode failure at the watch boundary in both
helper copies, preserve the bounded finding, and add source, packaged, work
close, and Stop regressions.

### P1-02 — active-claim repeated-failure authority is discarded

The active repair claim declares both:

- `escalation_triggers: [..., repeated_failure]`; and
- `defect_signatures:
  [defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694]`.

The exact candidate's `_active_work_contexts()` resolves the claim to its unit
file and appends only the unit metadata. It drops the claim's triggers,
signatures, and Compound references. The unit and parent task carry neither
`repeated_failure` nor a defect signature in the exact candidate.

Read-only reproduction against this worktree returned the following for both
explicit-unit and inferred-claim paths:

```text
repeat_failure.required = false
repeat_failure.defect_signatures = []
repeat_failure.escalation_triggers = [data_integrity, cross_cutting]
```

Feeding that result to `decide()` with substantial churn and a linked generic
review returned `approve (closure-record-present)`. Thus a claim that is
canonically marked as a repeated failure can take the ordinary review-only
path. Merge claim and work-item authority conservatively, or persist the claim
authority into canonical work metadata before assessment, and cover explicit
work-id, inferred single-claim, work close, and Stop paths.

### P1-03 — current Compound cannot close the parent task

This is a current W4 lifecycle finding outside implementation commit
`0ac8e507`, but it blocks release readiness. The new current-work record
`COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b`
contains only `UNIT-TASK-AR-654-001` in `work_ids`. A read-only call through
the exact task closeout validator produced:

```text
...COMPOUND-20260801-002336-...json:
closeout:compound-work-mismatch:TASK-AR-654
```

The unmerged record must directly include both `TASK-AR-654` and
`UNIT-TASK-AR-654-001`, followed by deterministic index regeneration and a
passing Compound store check.

### P1-04 — Markdown reports are stored as JSON verification evidence

The current unit's `evidence_refs` includes the Markdown skeptic report and
W4a report. `_validate_done_closeout()` JSON-decodes every `evidence_refs`
entry. A read-only validation therefore produced two
`closeout:evidence-invalid-json` findings, one for each Markdown file.

Keep machine verification receipts in `evidence_refs`; move W4a and skeptic
reports to the review/report lane used by closeout. Re-run the actual unit
closeout validator before requesting the next W4b.

## Independently green evidence

The findings above do not invalidate the bounded physical-line repair itself:

- `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py
  -q -k 'splitlines_separator_markers or physical_line_endings'` — `70 passed,
  738 deselected`;
- `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py
  -q` — `808 passed`;
- the registered eight-file verification selection — `1032 passed`;
- `python scripts/compound_record.py check` — `compound-record: pass`;
- `python scripts/template_mirror_gate.py --check` — 84 expected/common, 81
  identical, 3 intentional, 0 findings;
- `python scripts/regen_host_lock_if_needed.py --check` — current;
- `python scripts/runtime_asset_usage.py --check` — pass, 39 assets, 0 block,
  0 watch; and
- `git diff --check 0ac8e507^ 0ac8e507` — pass.

Python's actual `str.splitlines()` boundary enumeration contains LF, CR, and
exactly the eight separately guarded separators: VT, FF, FS, GS, RS, NEL,
U+2028, and U+2029. The source and packaged helpers both have SHA-256
`30913e6d5ff776124beccb5f736846963882bac20c3da68af982177e3dde5b4e`.
Canonical LF and CRLF controls pass; lone CR and all eight noncanonical
separators fail closed in the covered cases.

The `.json` watch branch is unchanged by the implementation commit, and the
complete consumer files retain JSON duplicate-key and authority-normalization
coverage. Record immutability, deterministic index rebuild, and read-only
legacy fallback tests also remain green. The RED commit changes tests only;
the implementation commit changes no test, preserving failure-first ordering.

The reviewed W4a has SHA-256
`9eb40528ee7b8ccd3c1b334e87b53c045ef0fcbf157ca64cdf52a4e55e92513b`.
Its machine evidence has SHA-256
`16015c9c7ebb6bb58691aefc89e870aa7708ee264b15c5f2ef1f65596138e893`.
Those receipts support the green matrix but do not cover the four blocking
findings above.

## Required next candidate

Before a fresh independent W4b:

1. convert malformed UTF-8 into the same bounded invalid-watch result through
   source, packaged, work close, and Stop paths;
2. preserve active-claim repeated-failure triggers, signatures, and relevant
   Compound links when resolving closure contexts;
3. link the unmerged current-work Compound directly to both task and unit and
   regenerate/check its index;
4. separate JSON verification receipts from Markdown review reports and prove
   both unit and task closeout validation are clean; and
5. replay the 70-case matrix, both full consumer files, registered selection,
   store, mirror, and host-lock checks on one exact new candidate tree.

No merge, claim release, work close, consumer-repository mutation, version,
tag, publication, push, deployment, or external action is authorized by this
`REVISE` report.
