---
title: TASK-AR-608 Skeptic and Adversarial W4b
date: 2026-07-23
signal: fail
score: 74
task_id: TASK-AR-608
verified_head: 1c9ebc1c9b0841c8d64de3ed3b6f3b8ab4aad7e7
implementation_sha: 871b6b9ed863647321129319ff37fac4e0473acc
failure_first_sha: 45085b33e0e29c48485edbc322b23026d0023c95
verified_by: codex-task-ar-608-skeptic-20260723
worker: codex-root-task-ar-608
role: skeptic
verdict: REJECT
tags: [task-ar-608, skeptic, adversarial, frontmatter, parser, comments, parity]
---

# TASK-AR-608 Skeptic and Adversarial W4b

## Verdict

**REJECT** at exact HEAD
`1c9ebc1c9b0841c8d64de3ed3b6f3b8ab4aad7e7`, implementation commit
`871b6b9ed863647321129319ff37fac4e0473acc`.

The implementation fixes the reported leading quoted-scalar defect and passes
the registered suite, root/template parity, and lock verification. Approval is
blocked because its quote-start heuristic changes the legacy behavior of valid
unquoted values: a quote that appears after plain scalar content can suppress
the first `#` comment marker. This directly violates the registered acceptance
criterion that unquoted comments retain their current behavior.

## Findings

### [P1] Mid-plain-scalar quotes are misclassified as quote delimiters

`strip_comment()` opens quote state when the current character is a quote and
the previous character is whitespace. It does not first establish whether
plain scalar content has already started. Consequently, quotes occurring after
plain content are treated as a new YAML quoted scalar even though they are
ordinary characters in that plain scalar.

AST-extracted `strip_comment()` from the failure-first revision
`45085b33` was used as the legacy comparison. The exact implementation and
host-template functions produced identical but incompatible results:

```text
input:  plain 'PR #167' # outside
legacy: "plain 'PR " (trailing space)
new:    "plain 'PR #167' " (trailing space)

input:  plain "PR #167" # outside
legacy: 'plain "PR ' (trailing space)
new:    'plain "PR #167" ' (trailing space)

input:  owner ' fragment # outside
legacy: "owner ' fragment " (trailing space)
new:    owner ' fragment # outside
```

The third case is especially damaging: an unmatched apostrophe after plain
content holds the scanner in quote state to end-of-line and silently preserves
the entire comment. The behavior is deterministic, but it is the wrong
deterministic result for an unquoted scalar and regresses the old first-hash
removal contract.

Required rework: track whether the current scalar or flow item has consumed
plain content. Open single/double quote state only at a scalar/item start
(after the key delimiter or a flow/list delimiter plus optional whitespace),
not after arbitrary whitespace inside an existing plain scalar. Add the three
counterexamples above to both-parser coverage while retaining the current
leading-quote, escape, doubled-single-quote, flow-list, malformed-leading-quote,
and unquoted-comment cases. This remains a lexical scanner change and does not
require a general YAML dependency.

## Measurable Validation

| Metric | Threshold | Measured value | Source | Status | Next action |
| --- | --- | --- | --- | --- | --- |
| Registered focused suite | all tests pass | 15/15 passed | `python -m pytest tests/test_backlog_board_tasksets.py -q` | pass | retain |
| Failure-first causality | old parser truncates quoted hash | `"PR #167 intact"` became `"PR ` at `45085b33`; implementation preserves it | AST-extracted baseline probe | pass | retain |
| Requested quote/escape boundary matrix | all cases pass in root and template | 9/9 passed | independent in-memory probe | pass | retain |
| Unquoted-comment compatibility | all adversarial cases equal legacy result | 0/3 compatible | independent legacy/current probe | **fail** | restrict quote starts and add regressions |
| Root/template scanner parity | identical function behavior/source | identical | AST/source parity probe | pass | retain |
| Generated host lock | no drift | current | `python scripts/regen_host_lock_if_needed.py --check` | pass | retain |
| Implementation scope | only declared target files | 4/4 declared files, 0 extra | `git diff --name-status 45085b33..871b6b9e` | pass | retain |

## Passing Boundaries

Independent probes passed for both root and template parsers:

- a plain apostrophe without quote-start context: `owner's value # outside`;
- a leading closed double quote followed by an outside comment;
- odd escaped double quotes and even backslash parity before a closing quote;
- YAML-style doubled single quotes in a leading single-quoted scalar;
- mixed quoted entries and an outside comment in a flow list;
- a malformed leading double quote, which deterministically preserves the
  remaining text rather than truncating the quoted hash;
- ordinary unquoted `plain value # outside`, which still removes the comment;
  and
- byte-equivalent behavior of the root/template `strip_comment()` functions.

These passing cases establish that the reported GitHub #298 path is repaired.
They do not cover or override the mid-plain-scalar heuristic regression above.

## Commands and Evidence

```text
python -m pytest tests/test_backlog_board_tasksets.py -q
15 passed in 0.99s

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --check 45085b33..871b6b9e
pass

git diff --name-status 45085b33..871b6b9e
M scripts/backlog_board.py
M src/agent_runtime/templates/project/scripts/backlog_board.py
M tests/fixtures/host/agent_runtime.lock.json
M tests/test_backlog_board_tasksets.py
```

The independent in-memory probe dynamically imported both current parser
modules, AST-extracted only `strip_comment()` from
`45085b33:scripts/backlog_board.py`, and exercised the requested and heuristic
matrices without writing test or implementation files. The requested matrix
passed; the three legacy-compatibility checks above failed.

Both W4a verification records parse as passing evidence, identify worker
`codex-root-task-ar-608`, and record the same 15-test suite and current host
lock with return code zero:

- `reviews/VERIFY-2026-07-23-task-ar-608-20260723063647.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723063712.json`

## Scope and Mutation Boundary

The implementation delta from `45085b33` to `871b6b9e` changes exactly the
declared root parser, host-template parser, focused test, and generated host
lock. HEAD after the implementation contains only task/unit W4a state,
verification JSON, and the generated review index. No task-scope expansion was
found.

This skeptic pass created only
`reviews/ROLE-REVIEW-2026-07-23-TASK-AR-608-SKEPTIC.md`. It did not modify
implementation files, tests, task/unit metadata, runtime state, W4a evidence,
or `reviews/INDEX.md`.
