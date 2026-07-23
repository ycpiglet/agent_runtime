---
title: TASK-AR-617 Final Skeptic Adversarial W4b
date: 2026-07-23
signal: fail
score: 74
task_id: TASK-AR-617
verified_head: dbdb6168599fa17556d1a7c366c86070123b5849
implementation_sha: b27c4754462c1c35266a88dee47801098bd31844
failure_first_sha: bbbecb449a6671786ccfa22dbffaea550be147b3
verified_by: codex-task-ar-617-skeptic-final-20260723
worker: codex-root-task-ar-617-final
role: skeptic
verdict: REWORK
tags: [task-ar-617, skeptic, adversarial, final-w4b, frontmatter, data-integrity]
---

# TASK-AR-617 Final Skeptic Adversarial W4b

## Verdict

**REWORK — 74/100** at exact clean W4a HEAD
`dbdb6168599fa17556d1a7c366c86070123b5849`.

The previous reserved-marker leak is fixed for encoded unsafe strings. Writer
output now reaches backlog, org-model, root/template work-schema, attention,
and dispatch consumers with identical values for hashes, quotes, whitespace,
bracket-like scalars, reserved-marker originals, Unicode, and all eleven
`splitlines()` boundaries.

One blocking class remains: safe type-like **strings** are emitted without the
reserved marker and are coerced by `org_model_gate` into booleans or integers.
The backlog and work-schema parsers keep the same inputs as strings. The drift
reaches attention display and worker orders, directly violating the task's
acceptance criterion that metadata remain exact "without type-like coercion."

## Blocking Counterexample

The writer emitted these Python strings as ordinary unquoted scalar/list
values. The parsers then disagreed:

| Original string | Emitted form | Backlog | Org-model | Work-schema | Result |
|---|---|---|---|---|---|
| `true` | `true` | `str: true` | `bool: True` | `str: true` | **Block** |
| `True` | `True` | `str: True` | `bool: True` | `str: True` | **Block** |
| `false` | `false` | `str: false` | `bool: False` | `str: false` | **Block** |
| `False` | `False` | `str: False` | `bool: False` | `str: False` | **Block** |
| `0` | `0` | `str: 0` | `int: 0` | `str: 0` | **Block** |
| `-7` | `-7` | `str: -7` | `int: -7` | `str: -7` | **Block** |
| `007` | `007` | `str: 007` | `int: 7` | `str: 007` | **Block** |
| `null` | `null` | `str: null` | `str: null` | `str: null` | Pass |
| `None` | `None` | `str: None` | `str: None` | `str: None` | Pass |
| `[planned, done]` | reserved encoding | exact string | exact string | exact string | Pass |

The end-to-end operational probe used legitimate free-form string metadata:

```text
title: "true"
context: "False"
target_files: ["007"]
acceptance: ["-7"]
```

After writer serialization:

- canonical backlog parsing retained `"true"`, `"False"`, `"007"`, and
  `"-7"` as strings;
- attention received title `True` as a boolean;
- the worker order received context `False` as a boolean;
- the worker order received target files `[7]`, losing the two leading zeroes;
- the worker order received acceptance `[-7]` as an integer list.

This can change UI representation, dispatch instructions, footprint identity,
and acceptance semantics. It is therefore a release blocker rather than a
cosmetic legacy difference.

## Writer-to-Consumer Adversarial Matrix

Apart from the type-like class above, the final implementation passed 23 value
classes against five parsers:

| Value family | Cases | Backlog | Template backlog | Org-model | Root schema | Template schema |
|---|---:|---:|---:|---:|---:|---:|
| Plain and Unicode | 2 | Pass | Pass | Pass | Pass | Pass |
| Hash/quote/Unicode combination | 1 | Pass | Pass | Pass | Pass | Pass |
| Leading/trailing whitespace | 2 | Pass | Pass | Pass | Pass | Pass |
| Bracket-like scalar | 1 | Pass | Pass | Pass | Pass | Pass |
| Leading/trailing quote | 2 | Pass | Pass | Pass | Pass | Pass |
| Internal tab | 1 | Pass | Pass | Pass | Pass | Pass |
| Reserved-marker original | 2 | Pass | Pass | Pass | Pass | Pass |
| Serialized-token literal | 1 | Pass | Pass | Pass | Pass | Pass |
| Splitlines boundaries | 11 | Pass | Pass | Pass | Pass | Pass |

That is 115 direct parser equality assertions. Each case also passed three
successive byte-identical rewrite cycles through `work._frontmatter` and the
canonical backlog parser.

The actual previous-blocker chain also passed:

- attention displayed `Blocked #1 "quoted"` exactly;
- dispatch preserved context `Handle issue #1 "exactly"`;
- dispatch preserved target file `src/#generated.py`;
- dispatch preserved acceptance `Preserve # markers`.

## Splitlines and Physical-Line Safety

Scalar and block-list values containing every Python `str.splitlines()`
boundary passed across all five parsers:

| Name | Code point(s) | Result |
|---|---|---:|
| LF | U+000A | Pass |
| CR | U+000D | Pass |
| CRLF | U+000D U+000A | Pass |
| VT | U+000B | Pass |
| FF | U+000C | Pass |
| FS | U+001C | Pass |
| GS | U+001D | Pass |
| RS | U+001E | Pass |
| NEL | U+0085 | Pass |
| LS | U+2028 | Pass |
| PS | U+2029 | Pass |

Rendered NEL, LS, and PS values contained `\u0085`, `\u2028`, and `\u2029`
respectively, with no raw separator and no extra physical line.

## Marker and Legacy Compatibility

The following passed across backlog, org-model, and root/template work-schema
readers:

- original values beginning with the reserved marker are encoded with an
  additional marker layer and decode to the exact original;
- marker-prefixed values containing a hash also remain exact;
- a string whose content is itself a serialized marker token survives without
  accidental single decoding;
- valid writer tokens decode once and only once;
- invalid marker-like JSON fails closed to the same legacy string value;
- ordinary quoted strings are not mistaken for writer tokens;
- the established escaped-double-quote result remains unchanged;
- safe non-type-like values are not unnecessarily re-represented.

## Root and Template Parity

- `decode_encoded_work_scalar`, `parse_scalar`, and `parse_header_block` have
  identical ASTs in root/template backlog parsers.
- Root and template `work_schema_gate.py` files are byte-identical.
- The generated-host lock is current.
- The final consumer implementation changes only `org_model_gate.py`,
  root/template `work_schema_gate.py`, and the host lock; failure-first adds the
  four focused consumer test files and preserves prior review evidence.
- `git diff --check` passed.

## Failure-First Causality

Exact failure-first commit
`bbbecb449a6671786ccfa22dbffaea550be147b3` is an ancestor of the verified
HEAD. Its four newly added consumer regressions were executed from an isolated
archive and produced:

```text
4 failed in 1.57s
```

The failures covered attention title, dispatch worker fields, org-model
scalar/list decoding, and root/template work-schema decoding. Implementation
`b27c4754462c1c35266a88dee47801098bd31844` makes those exact tests pass, so
the marker-leak fix has valid failure-first causality.

The new type-like blocker has no failure-first or current regression coverage.

## W4a Freshness and Independent Commands

Latest task/unit evidence was created after the final implementation and at the
exact verified HEAD:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723093020.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723093043.json`

Both identify `codex-root-task-ar-617-final` and report all registered commands
passing. Independent rerun results were:

```text
python -m pytest tests/test_work_registration.py tests/test_work_verify.py \
  tests/test_work_close.py tests/test_backlog_board_tasksets.py \
  tests/test_org_model_gate.py tests/test_attention_inbox.py \
  tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
80 passed in 18.10s

python scripts/work_schema_gate.py --check
work-schema-gate: pass
findings=0
warnings=0

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

Per instruction, the complete local suite was not run and is not claimed.

## T3 and Regression Assessment

The cross-consumer T3 replan correctly expanded the marker decoder to
org-model and root/template work-schema readers while preserving attention and
dispatch production code. That plan closed the known encoded-marker blocker.

However, it explicitly preserved legacy non-marker boolean/integer coercion
without reconciling that behavior with writer-originated free-form strings.
This leaves the task's no-type-coercion acceptance criterion unsatisfied. The
focused 80-test suite contains marker-bearing hash/quote cases but no
writer-originated free-form `true`, `False`, `007`, or signed-integer cases.

The next replan should distinguish actual boolean/integer metadata from string
metadata at emission. Because `_frontmatter` already has a separate branch for
Python booleans, type-like Python strings can be protected without changing the
intended representation of true boolean fields. The exact design remains a
planner decision.

## Residual Risks

- Manually placing a reserved encoded token inside a flow list is interpreted
  differently by the independent lightweight parsers. The writer emits block
  lists, so this is not the demonstrated blocker, but the manual compatibility
  boundary should remain documented.
- The legacy quote trimmer still loses a trailing escaped quote when it is
  immediately adjacent to the outer quote. This predates TASK-AR-617 and the
  final implementation does not worsen it.
- Several consumers still rely on field-agnostic coercion. Future emitter
  changes can reopen semantic drift unless writer-to-consumer matrices include
  both unsafe encoded strings and syntactically safe type-like strings.

## Measurable Validation

| Metric | Threshold | Measured | Source | Status | Next action |
|---|---:|---:|---|---|---|
| Unsafe cross-parser equality | 100% | 115/115 | adversarial probe | Pass | None |
| Splitlines equality | 11/11 × 5 parsers | 55/55 | direct matrix | Pass | None |
| NEL/LS/PS physical safety | 3/3 | 3/3 | rendered-text inspection | Pass | None |
| Rewrite idempotence | 3 cycles per case | all byte-identical | direct matrix | Pass | None |
| Attention/dispatch marker path | 4/4 fields | 4/4 exact | end-to-end probe | Pass | None |
| Type-like cross-parser equality | 10/10 | 3/10 | adversarial probe | **Fail** | Replan emitter string protection |
| Type-like operational equality | 4/4 fields | 0/4 | attention/dispatch probe | **Fail** | Add end-to-end regressions |
| Root/template parity | exact | exact | AST/byte comparison | Pass | None |
| Failure-first marker causality | 4 pre-fix failures | 4 failures | isolated archive | Pass | None |
| Focused W4a | all pass | 80 passed | pytest | Pass | None |
| Schema and host-lock gates | both pass | both pass | registered gates | Pass | None |
| Full suite | not requested | not run | instruction boundary | N/A | None |

## Required Rework

1. Record a narrow T3 amendment for writer-originated type-like strings.
2. Preserve free-form string identity across backlog, org-model, work-schema,
   attention, and dispatch without changing actual boolean/integer fields.
3. Add scalar and block-list tests for `true`, `False`, `0`, signed integers,
   and leading-zero numeric strings through the real writer-consumer chain.
4. Refresh W4a and repeat the focused independent consumer matrix on a new
   clean HEAD.
