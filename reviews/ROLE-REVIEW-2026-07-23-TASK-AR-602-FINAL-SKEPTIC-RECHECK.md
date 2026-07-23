---
status: hold
origin_type: independent_final_skeptic_recheck
origin_ref: reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
signal: fail
score: 86
reviewed_head: 8abc8ad5df66e432fd2d44b2969615c4aec35396
previous_reviewed_head: 7a5935b05cdd037b25c8a1521b818319bb948aec
decision: closeout_hold
tags:
  - task-ar-602
  - w4b
  - skeptic
  - recheck
  - provenance
  - frontmatter
---

# TASK-AR-602 Final Skeptic Recheck Addendum

## Gate

This addendum rechecks only the HOLD conditions from
`ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md` at exact repair HEAD
`8abc8ad5df66e432fd2d44b2969615c4aec35396`. It does not revise or replace the
earlier report.

## Readiness decision

**TASK-AR-602 closeout remains HOLD, 86/100.**

The damaged TASK-AR-602 values are correctly restored, quoted, and
round-trip-safe. The exhaustive taskset expectation and focused gates are also
green. HOLD is not lifted because the TASK-AR-622 follow-up is not presently
dispatch-ready and its acceptance contract can pass without preventing the
legacy unquoted-scalar failure that caused this incident.

## Previous blocker resolution

| Previous blocker | Recheck | Result |
| --- | --- | --- |
| Task `origin_ref` lost issue/PR suffix | Exact value restored as a quoted scalar | resolved |
| Unit `origin_ref` lost issue/PR suffix | Exact value restored as a quoted scalar | resolved |
| Unit `context` collapsed to `GitHub` | Full original release rationale restored as a quoted scalar | resolved |
| `_frontmatter` rewrite could lose the repaired values | Parse → `scripts.work._frontmatter` → `backlog_board.parse_frontmatter` preserves exact metadata across repeated rounds | resolved |
| General defect had no registered owner | TASK-AR-622 and UNIT-TASK-AR-622-001 are registered with reservation, classification, backlog, taskset, and T0 record | structurally resolved |
| Follow-up could actually prevent the observed class | Current acceptance is limited to parser-visible values and does not require legacy unsafe-input detection or migration | unresolved |
| Follow-up T0 is valid for later T2 dispatch | Direct plan-assumption check fails on its design anchor | unresolved |
| Exhaustive taskset expectation stale | New taskset ID is present and all focused taskset tests pass | resolved |

## Independently passed checks

### Exact provenance restoration

Both task and unit now parse to the exact original value:

```text
chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
```

The unit `context` also parses exactly to:

```text
GitHub #280 approved v0.7.0 from an older SHA; current main has additional fixes, so the candidate must be rebuilt and verified only after every open intake item is integrated.
```

The added double quotes change only the safe physical representation, not the
value. The restored values match the pre-loss repository text exactly.

### Serializer/parser round trip

For both repaired files, the recheck performed:

1. `backlog_board.parse_frontmatter(current text)`;
2. `scripts.work._frontmatter(parsed metadata)`;
3. `backlog_board.parse_frontmatter(serialized text)`;
4. a second serialization and parse.

The metadata dictionaries, full origin references, and full unit context
remained equal at every step. A separate probe containing `#`, an apostrophe,
brackets, boolean-like and numeric-like text, and escaped quotes also survived
as both a scalar and list item. The serializer used the encoded work-scalar
marker as designed.

### Registration and focused gates

- TASK-AR-622 has a fulfilled reservation and one worker-ready unit.
- Initiative, taskset definition, classifier entries, generated board entry,
  registration review, unit, and plan record all exist.
- The unit is bounded to registration/verify/close scalar integrity and
  prohibits bulk historical rewrites and evidence-schema changes.
- `tests/test_work_registration.py`, `tests/test_work_verify.py`,
  `tests/test_work_close.py`, and `tests/test_backlog_board_tasksets.py`:
  **37 passed**.
- Task identity: pass, findings 0.
- Work-item classifier: pass, findings 0.
- Taskset work gate: pass, findings 0.
- Work schema gate: pass, findings 0 and warnings 0.
- Owner governance: exit 0.
- The exhaustive taskset expectation adds only
  `TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY`, matching the registered
  active taskset.

## Remaining blocker 1: T0 is byte-drifted

TASK-AR-622 has a T0 assumption set with the intended three anchors:

- the taskset registration design record;
- `scripts/task_claim_dispatcher.py`;
- `scripts/work.py`.

Its policy is correctly fail-closed with `block_dispatch_on_drift`. However,
the direct check fails:

```text
plan-assumption-gate: fail
anchor-hash-changed:
reviews/REVIEW-2026-07-23-taskset-ar-work-frontmatter-scalar-integrity-registration.md
```

The recorded digest is `9f9f8947...`; the current file digest is
`32a0ac3c...`. This is not a content-plan edit: `9f9f8947...` exactly equals
the digest of the current file converted to CRLF, while the checked-out file is
LF because `.gitattributes` declares `text=auto, eol=lf`. The snapshot captured
pre-commit Windows line endings and Git normalization changed the bytes.

This is a false-positive drift rather than semantic plan drift, but the result
is operationally real: T2 must refuse a TASK-AR-622 claim until a replan/T3
record re-anchors the normalized file. A fail-closed but immediately stale T0
cannot be reported as a fully valid dispatch registration.

## Remaining blocker 2: TASK-AR-622 can miss the original defect

The existing implementation and tests already prove that:

- structured registration serializes hash-bearing values safely;
- quoted or encoded parser-visible values survive verify and close rewrites.

Those tests predate this repair. The TASK-AR-602 incident occurred because a
legacy unquoted scalar was first parsed as:

```text
origin_ref: chat:2026-07-19-all-open-intake; github:
```

Only after that loss did verification serialize the parser-visible value. The
serializer then preserved the already-truncated value exactly. Therefore the
current TASK-AR-622 acceptance statement, “preserve the exact parser-visible
scalar value,” can pass without detecting or preventing the incident class.

The follow-up must explicitly choose and test one of these safe contracts:

1. fail closed before verify/close rewrites any legacy work record containing
   an unsafe unquoted `#` scalar; or
2. perform a reviewed, explicit migration from an authoritative raw value
   before lifecycle rewriting.

It must not infer discarded content or silently bless the truncated parsed
value. Until this is added to the planner-approved task/unit acceptance,
TASK-AR-622 does not fully absorb the general defect.

## Warnings and residual risks

- `git diff --check` on the repair range reports one extra blank line at EOF in
  `REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md`.
  This is non-semantic but should be cleaned before final integration.
- A future lifecycle rewrite will encode the safely quoted values using the
  internal marker. Human-readable physical form may change, while the parsed
  value remains exact.
- The current branch still has the expected active TASK-AR-602 claim,
  closeout worktree, and divergence. W5/W6 cleanup has not yet occurred.
- The public v0.7.0 release remains valid and must not be changed because of
  these internal metadata issues.

## Required next actions

1. Amend the TASK-AR-622 task/unit contract to cover legacy unquoted
   hash-bearing scalars before parse/rewrite loss, using fail-closed detection
   or explicit reviewed migration.
2. Record that amendment in a replan review and re-record the T3 snapshot
   against the committed LF-normalized design record.
3. Require
   `plan_assumption_gate.py --check --taskset
   TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY` to pass.
4. Add a focused regression whose starting record contains the unsafe legacy
   representation and prove the chosen contract prevents silent truncation.
5. Remove the non-semantic EOF whitespace finding and rerun the 37 focused
   tests plus identity/classifier/taskset/schema/governance gates.
6. Request a final exact-HEAD addendum. Only then release the TASK-AR-602
   claim and continue W5/W6 cleanup.

## Final verdict

**Provenance repair at `8abc8ad5df66e432fd2d44b2969615c4aec35396`:
PASS. TASK-AR-602 closeout: HOLD.**

The previous data is restored and currently safe. HOLD remains because the
general follow-up's T0 is stale by line-ending normalization and its acceptance
can pass while remaining blind to the legacy parse-before-rewrite loss.
