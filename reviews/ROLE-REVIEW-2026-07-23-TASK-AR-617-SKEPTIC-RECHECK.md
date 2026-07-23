---
title: TASK-AR-617 Skeptic Adversarial W4b Recheck
date: 2026-07-23
signal: fail
score: 68
task_id: TASK-AR-617
verified_head: ed914753e4c2415885195566fa0bd0af63596f50
implementation_sha: 4c6f2035b7823e12e91d707af68077b422f33a13
failure_first_sha: eaeed365fb4c718f43ed13d3f79d8860029fc1d2
verified_by: codex-task-ar-617-skeptic-recheck-20260723
worker: codex-root-task-ar-617-rework
role: skeptic
verdict: REWORK
tags: [task-ar-617, skeptic, adversarial, w4b, recheck, frontmatter, data-integrity]
---

# TASK-AR-617 Skeptic Adversarial W4b Recheck

## Verdict

**REWORK — 68/100** at exact refreshed W4a HEAD
`ed914753e4c2415885195566fa0bd0af63596f50`.

The narrow splitline-boundary rework succeeds: all eleven Python
`str.splitlines()` boundaries round-trip through scalar and block-list fields,
and `ensure_ascii=True` prevents NEL, U+2028, and U+2029 from becoming physical
frontmatter lines. However, the reserved marker is decoded only by
`backlog_board`. Existing backlog consumers that use `org_model_gate` or their
own lightweight parser receive the marker representation instead of the
canonical value. This corrupts an actual attention-inbox title and the context,
target files, and acceptance criteria placed in a worker order.

That cross-consumer semantic mismatch is a blocking data-integrity defect. No
approval is possible at this HEAD.

## Blocking Counterexample

The probe serialized this canonical metadata through
`scripts/work.py::_frontmatter`:

```text
title: Fix issue #167
context: Preserve issue #168
target_files: [src/issue #168.py]
acceptance: [Keep PR #169 exactly]
```

`backlog_board.parse_frontmatter` returned every original value. In contrast,
`org_model_gate.parse_frontmatter` and `work_schema_gate._frontmatter` returned:

```text
title: \u001eagent-runtime-work-scalar-v1:Fix issue #167
context: \u001eagent-runtime-work-scalar-v1:Preserve issue #168
target_files:
  - \u001eagent-runtime-work-scalar-v1:src/issue #168.py
acceptance:
  - \u001eagent-runtime-work-scalar-v1:Keep PR #169 exactly
```

The mismatch reaches user- and worker-facing behavior:

- `attention_inbox._load_tasks` and `_item` display the marker-bearing title.
- `dispatch_gate._front_meta` passes marker-bearing unit metadata onward.
- `org_orchestrator.build_order` emits marker-bearing `context`,
  `target_files`, and `acceptance` to the worker.
- `work_schema_gate` passes while observing marker-bearing values, so its green
  result does not detect this semantic drift.

This is not merely byte-level serialization churn. A lower-cost worker can be
given different instructions and file paths from those stored canonically.

## Counterexample Matrix

| Boundary | Expected | Measured at `ed914753` | Result |
|---|---|---|---|
| `backlog_board` scalar decode | original value | original value | Pass |
| `backlog_board` block-list decode | original list item | original list item | Pass |
| generated-host parser | same as root parser | same changed-function AST and values | Pass |
| `org_model_gate` scalar | original value | literal marker plus original | **Block** |
| `org_model_gate` block list | original item | literal marker plus original | **Block** |
| attention-inbox title | `Fix issue #167` | marker-bearing title | **Block** |
| worker context | `Preserve issue #168` | marker-bearing context | **Block** |
| worker target file | `src/issue #168.py` | marker-bearing path | **Block** |
| worker acceptance | `Keep PR #169 exactly` | marker-bearing criterion | **Block** |
| schema-gate parser parity | canonical values | marker-bearing values, gate still green | **Block** |

## Splitline Rework Matrix

The new emitter boundary set was exercised as both a scalar and a block-list
item against root and template parsers:

| Separator | Code point(s) | Root | Template | Physical-line escape |
|---|---|---:|---:|---:|
| LF | U+000A | Pass | Pass | Pass |
| CR | U+000D | Pass | Pass | Pass |
| CRLF | U+000D U+000A | Pass | Pass | Pass |
| VT | U+000B | Pass | Pass | Pass |
| FF | U+000C | Pass | Pass | Pass |
| FS | U+001C | Pass | Pass | Pass |
| GS | U+001D | Pass | Pass | Pass |
| RS | U+001E | Pass | Pass | Pass |
| NEL | U+0085 | Pass | Pass | `\u0085` present, raw U+0085 absent |
| LS | U+2028 | Pass | Pass | `\u2028` present, raw U+2028 absent |
| PS | U+2029 | Pass | Pass | `\u2029` present, raw U+2029 absent |

Every generated document retained exactly five physical lines for the scalar
plus block-list fixture. Re-emitting the parsed metadata produced byte-identical
frontmatter.

## Marker, Idempotence, and Compatibility Matrix

The following passed independently for both root and generated-host parsers:

- marker-prefixed original values, including a marker-prefixed value containing
  a hash, are double-prefixed on disk and decode back to the exact original;
- a literal string that itself equals a serialized marker token survives
  encoding and decoding without one layer being lost;
- twelve ordinary/adversarial scalar and list classes passed three successive
  byte-idempotent rewrite cycles;
- Unicode, quote/hash combinations, leading/trailing whitespace, bracket-like
  scalars, leading/trailing quotes, and internal tabs preserve exact values;
- invalid marker-like JSON is not decoded and retains the legacy parser result;
- ordinary quoted manual strings and ordinary textual marker-like prefixes are
  not mistaken for reserved encodings;
- the established escaped-double-quote representation remains unchanged;
- ordinary flow-list values survive a flow-to-block rewrite as the same parsed
  list;
- safe scalar/list metadata produces byte-for-byte the same representation as
  the pre-change emitter, so measured safe-value churn is zero.

A valid JSON string carrying the exact reserved control-prefix is intentionally
decoded. Values entering through `work.py` that genuinely begin with that
prefix are protected by an additional prefix layer, so the application input
round-trips. Manually authoring the reserved wire representation remains a
documented collision boundary rather than an ordinary scalar path.

## Failure-First Causality

The exact rework failure-first commit
`eaeed365fb4c718f43ed13d3f79d8860029fc1d2` was archived into an isolated
directory. Its expanded registration regression produced:

```text
1 failed in 1.68s
```

The failure occurred at the acceptance-list equality check; the first failing
splitline value was truncated from `left<vertical-tab>right` to `left`.
Implementation `4c6f2035b7823e12e91d707af68077b422f33a13` changes only
`scripts/work.py`; the failure-first range also adds only the focused
registration regression. `git diff --check` passed.

The original T3 record names failure-first `28906fd4`, while the reachable
rebased lineage uses `451b2604`. Both objects still exist and the three
failure-first test blobs are byte-identical; isolated execution of each
produced the same three lifecycle failures. This preserves technical causality,
but the stale commit reference is a non-blocking provenance defect.

## W4a Evidence and Independent Commands

The refreshed W4a records were inspected:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723091656.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723091709.json`

Both identify `codex-root-task-ar-617-rework` and report all registered commands
passing. The same commands were independently rerun at exact HEAD:

```text
python -m pytest tests/test_work_registration.py tests/test_work_verify.py \
  tests/test_work_close.py tests/test_backlog_board_tasksets.py -q
33 passed in 9.43s

python scripts/work_schema_gate.py --check
work-schema-gate: pass
findings=0
warnings=0

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

A full local pytest run was started but deliberately terminated before a result
when the verifier was instructed to freeze this REWORK evidence. It is **not**
counted as a pass, timeout, or failure.

## T3 Scope Finding

The recorded T3 plan expanded the reader surface only to root/template
`backlog_board.py`. That is insufficient because the writer changes the wire
format of canonical work records and the repository has multiple active
frontmatter consumers. The next replan must enumerate every consumer that can
read `work.py` output, select one shared decode contract or a compatible wire
format, and add end-to-end assertions for at least:

- attention-inbox title display;
- dispatch-gate footprints;
- orchestrator worker context and acceptance;
- schema/gate observation of canonical values.

The current T3 boundary therefore needs another recorded scope amendment before
implementation resumes.

## Residual Risks

- Marker decoding inside flow-list items is intentionally absent. The writer
  emits block lists, so this is not the blocking path, but a manually moved
  reserved token from block to flow form changes interpretation.
- The legacy parser trims a scalar whose quoted content ends immediately with
  an escaped quote down to a trailing backslash. This behavior predates the
  patch and was not worsened, but it remains a manual-frontmatter compatibility
  limitation.
- The focused test suite does not exercise the custom-parser consumer graph;
  green W4a and schema-gate results therefore overstate end-to-end integrity.

## Measurable Validation

| Metric | Threshold | Measured | Source | Status | Next action |
|---|---:|---:|---|---|---|
| Splitlines scalar preservation | 11/11 per copy | 11/11 root, 11/11 template | adversarial matrix | Pass | None |
| Splitlines block-list preservation | 11/11 per copy | 11/11 root, 11/11 template | adversarial matrix | Pass | None |
| NEL/LS/PS physical-line safety | 3/3 | 3/3 | rendered-text inspection | Pass | None |
| Rewrite idempotence | 3 cycles per case | 3 cycles, byte-identical | direct matrix | Pass | None |
| Safe representation churn | 0 | 0 | pre/post emitter comparison | Pass | None |
| Root/template changed-function parity | exact | exact AST | parser inspection | Pass | None |
| Failure-first causality | target fails before fix | 1 focused failure | isolated `eaeed365` | Pass | None |
| Focused W4a suite | all pass | 33 passed | pytest | Pass | None |
| Schema and host-lock gates | both pass | both pass | registered gates | Pass | None |
| Cross-consumer canonical parity | 100% | 0/4 unsafe field classes | consumer probe | **Fail** | Replan and fix shared read contract |
| User/worker display parity | exact | title/context/path/acceptance differ | end-to-end probe | **Fail** | Add integration regressions |
| Full local suite | completed result | no completed result | terminated run | Not measured | Rerun after blocker fix |

## Required Rework

1. Replan the parser footprint around the actual consumer graph.
2. Prevent the marker from leaking through `org_model_gate` and other active
   readers, without reintroducing unsafe raw scalars.
3. Add consumer-level regressions for UI display and worker-order content.
4. Rerun W4a, the complete local suite to an actual terminal result, independent
   W4b, and this skeptic matrix on a new clean HEAD.
