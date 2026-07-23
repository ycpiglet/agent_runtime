---
title: TASK-AR-617 Skeptic Approval W4b
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-617
verified_head: 7f7be81a8166498a1dd98437dd82931207bcd66b
implementation_sha: 1ee8a666
failure_first_sha: 4f4f9128
verified_by: codex-task-ar-617-skeptic-approval-20260723
worker: codex-root-task-ar-617-type-rework
role: skeptic
verdict: APPROVE
tags: [task-ar-617, skeptic, adversarial, approval-w4b, frontmatter, data-integrity]
---

# TASK-AR-617 Skeptic Approval W4b

## Verdict

**APPROVE — 98/100** at exact clean HEAD
`7f7be81a8166498a1dd98437dd82931207bcd66b`.

No blocking counterexample remains. The key-aware emitter preserves all seven
requested type-like free-form strings through scalar, list, attention, and
dispatch paths while retaining the established boolean semantics of
`approval_required` and `security_sensitive` and the integer semantics of all
twelve declared numeric fields.

The earlier splitline, marker, quote/hash, whitespace, idempotence, and
cross-consumer fixes remain intact. Root/template parity, focused W4a, schema,
and generated-host lock checks all pass.

## Type-Like Free-Form Matrix

Each value was written into `title`, `summary`, `context`, `target_files`, and
`acceptance`. The serialized record was then read by root/template backlog,
org-model, and root/template work-schema parsers.

| Original string | Scalar type/value | List item type/value | Attention title | Worker context/path/acceptance | Result |
|---|---|---|---|---|---:|
| `true` | `str: true` | `str: true` | exact string | exact strings | Pass |
| `True` | `str: True` | `str: True` | exact string | exact strings | Pass |
| `false` | `str: false` | `str: false` | exact string | exact strings | Pass |
| `False` | `str: False` | `str: False` | exact string | exact strings | Pass |
| `0` | `str: 0` | `str: 0` | exact string | exact strings | Pass |
| `-7` | `str: -7` | `str: -7` | exact string | exact strings | Pass |
| `007` | `str: 007` | `str: 007` | exact string | exact strings | Pass |

Measured coverage:

- 175 free-form parser assertions: 7 values × 5 fields × 5 parsers;
- 28 operational assertions: 7 values × attention title plus three worker
  order field groups;
- every scalar and list item retained both exact value and Python `str` type.

The emitted type-like strings use the reserved work-scalar representation, so
`org_model_gate` returns before its legacy boolean/integer coercion step.

## Key-Aware Boolean and Numeric Semantics

The type protection is deliberately bypassed only for known typed fields.

Boolean checks covered both Python booleans and all four established textual
spellings for each field:

| Field | Inputs | Parsed operational type/value | Behavior | Result |
|---|---|---|---|---:|
| `approval_required` | `True`, `False`, `true`, `True`, `false`, `False` | matching `bool` | true remains approval-pending; false does not | Pass |
| `security_sensitive` | `True`, `False`, `true`, `True`, `false`, `False` | matching `bool` | true is owner-gate; false remains auto | Pass |

Numeric checks covered `7`, string `"7"`, leading-zero string `"007"`, and
signed string `"-7"` for every declared numeric exception:

```text
actual_cost, actual_hours, actual_tokens, budget_cap,
est_cost, est_hours, est_tokens, gate_failure_count,
order, reopened_count, rework_count, xp_value
```

All 48 cases reached `org_model_gate` as integers with the expected numeric
value. A combined `budget_cap="100"`, `est_tokens="500"` record remained
numeric and continued to trigger the over-budget owner gate.

Thus the fix protects free-form strings without turning actual boolean or
integer governance/measurement fields into strings.

## Failure-First Causality

Exact failure-first commit `4f4f9128` is an ancestor of the verified HEAD. Its
three type-like regressions were executed from an isolated archive and
produced:

```text
3 failed in 1.98s
```

The failures independently demonstrated:

- registered title `"true"` became boolean `True`;
- attention title `"true"` became boolean `True`;
- dispatch context `"False"` became boolean `False` before the remaining
  worker-order assertions could run.

Implementation `1ee8a666` changes only `scripts/work.py` plus focused
org-model and registration tests. The implementation has direct failure-first
causality and `git diff --check` passes.

## Regression Sampling

Sixteen representative prior-risk values were rechecked across all five
parsers and three byte-identical rewrite cycles:

- a combined hash/single-quote/double-quote scalar;
- leading and trailing whitespace;
- a bracket-like scalar;
- an original value beginning with the reserved marker;
- all eleven `str.splitlines()` boundaries: LF, CR, CRLF, VT, FF, FS, GS, RS,
  NEL, LS, and PS.

All passed as both scalar and block-list values. NEL, LS, and PS remained
escaped on disk (`\u0085`, `\u2028`, `\u2029`) and created no physical line.

The original reserved-marker value was encoded with an additional marker layer
and decoded exactly once, preserving the original. Repeated writer/parser
cycles remained byte-identical.

## Root and Template Parity

- Root/template backlog functions `decode_encoded_work_scalar`, `parse_scalar`,
  and `parse_header_block` have identical ASTs.
- Root/template `work_schema_gate.py` files are byte-identical.
- The generated-host lock is current.
- The key-aware writer is a root work-CLI concern and does not introduce a new
  template-only implementation surface.

## W4a Freshness and Independent Commands

The latest task/unit evidence is newer than implementation `1ee8a666` and
records exact-HEAD verification by `codex-root-task-ar-617-type-rework`:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723094020.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723094101.json`

The registered commands were independently rerun:

```text
python -m pytest tests/test_work_registration.py tests/test_work_verify.py \
  tests/test_work_close.py tests/test_backlog_board_tasksets.py \
  tests/test_org_model_gate.py tests/test_attention_inbox.py \
  tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
82 passed in 15.81s

python scripts/work_schema_gate.py --check
work-schema-gate: pass
findings=0
warnings=0

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

Per instruction, the complete local suite was not run and is not claimed.

## Residual Risks

- The boolean and numeric exception sets are explicit maintenance lists. A new
  typed schema field must be added to the relevant set or it will be protected
  as a string. This is fail-safe for data preservation but could delay adoption
  of new typed metadata until tests and the list are updated.
- The focused tests replace the prior attention/dispatch hash fixture with a
  writer-originated type-like fixture. Direct parser marker regressions plus the
  independent end-to-end hash/quote probe still cover the prior failure, but
  keeping both operational fixtures in the permanent suite would reduce future
  regression risk.
- The previously documented manual flow-list reserved-token and trailing
  escaped-quote limitations remain outside the writer-generated block-list
  contract. Neither was changed by this rework.

These are non-blocking maintenance risks; none contradicts the task's current
writer-generated work-record contract.

## Measurable Validation

| Metric | Threshold | Measured | Source | Status | Next action |
|---|---:|---:|---|---|---|
| Free-form type-like parser equality | 175/175 | 175/175 | adversarial matrix | Pass | None |
| Attention/dispatch type-like equality | 28/28 | 28/28 | operational probe | Pass | None |
| Boolean key semantics | 12/12 | 12/12 | key-aware probe | Pass | None |
| Numeric key semantics | 48/48 | 48/48 | key-aware probe | Pass | None |
| Budget risk behavior | owner-gate retained | owner-gate | dispatch probe | Pass | None |
| Prior-risk regression sample | 16/16 × 5 parsers | 80/80 | direct matrix | Pass | None |
| Rewrite idempotence | 3 cycles/value | all byte-identical | direct matrix | Pass | None |
| Splitlines coverage | 11/11 | 11/11 | direct matrix | Pass | None |
| Root/template parity | exact | exact | AST/byte comparison | Pass | None |
| Failure-first causality | pre-fix failures | 3 failures | isolated `4f4f9128` | Pass | None |
| Focused W4a | 82 passing | 82 passed | pytest | Pass | None |
| Schema and host-lock gates | both pass | both pass | registered gates | Pass | None |
| Full suite | not requested | not run | instruction boundary | N/A | None |

No further rework is required for TASK-AR-617 at this HEAD.
