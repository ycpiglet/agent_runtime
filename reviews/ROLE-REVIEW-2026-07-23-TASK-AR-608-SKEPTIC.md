---
title: TASK-AR-608 Skeptic and Adversarial W4b
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-608
verified_head: 98498904008fc6876104053953d3e53c047e7098
implementation_sha: 44d16a9abce8c539f812905b9c80f27cab147213
original_rejected_head: 1c9ebc1c9b0841c8d64de3ed3b6f3b8ab4aad7e7
original_implementation_sha: 871b6b9ed863647321129319ff37fac4e0473acc
remediation_rejected_head: 97b6bffa138de3b71117dd7b001e110eca825da5
remediation_rejected_implementation_sha: 097758859e1f5f54655623fe077599718ec82292
failure_first_sha: 45085b33e0e29c48485edbc322b23026d0023c95
structural_failure_first_sha: 7b50c8b1436b302d3ad37f113261de8a943aedb7
verified_by: codex-task-ar-608-skeptic-20260723
worker: codex-root-task-ar-608
role: skeptic
verdict: APPROVE
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

## Remediation Re-review

This section records the independent re-review of remediation implementation
`097758859e1f5f54655623fe077599718ec82292` at W4a HEAD
`97b6bffa138de3b71117dd7b001e110eca825da5`. The original REJECT narrative,
counterexamples, commands, and findings above remain unchanged as audit
history. The frontmatter now identifies the latest reviewed state while
retaining the original SHAs explicitly.

### Original Counterexample Closure

The remediation skips whitespace before deciding whether a quote follows a
structural delimiter. This closes all specifically requested regressions in
both the root and host-template parsers:

| Boundary | Expected | Result |
| --- | --- | --- |
| `plain 'PR #167' # outside` | legacy first-hash removal | pass |
| `plain "PR #167" # outside` | legacy first-hash removal | pass |
| `owner ' fragment # outside` | unmatched mid-plain quote does not hide comment | pass |
| leading single/double quoted scalar | quoted hash preserved, outside comment removed | pass |
| escaped double quote | escaped quote does not close scalar | pass |
| doubled single quote | doubled quote does not close scalar | pass |
| mixed flow list | quoted hashes preserved, outside comment removed | pass |
| plain outside comment | legacy comment removal | pass |
| root/template AST | identical `strip_comment()` functions | pass |

The independent requested matrix measured 9/9 passing cases. The focused suite
also expanded from 15 to 16 tests and passed independently. The host lock is
current.

### [P1] Residual delimiter-lookback false positives keep the fix incomplete

The remediation still does not track whether plain scalar content has already
been consumed. It only skips whitespace and inspects the preceding non-space
character. As a result, an ordinary hyphen or comma inside an already-started
plain scalar is mistaken for a structural list/flow delimiter:

```text
input:           plain - 'PR #167' # outside
legacy expected: "plain - 'PR " (trailing space)
09775885 actual: "plain - 'PR #167' " (trailing space)

input:           plain, "PR #167" # outside
legacy expected: 'plain, "PR ' (trailing space)
09775885 actual: 'plain, "PR #167" ' (trailing space)
```

Both root and template return the same incorrect results. A local PyYAML
reference parse independently produced `plain - 'PR` and `plain, "PR`,
confirming that the first hash is a comment boundary in these plain scalars.
The finding does not depend on PyYAML: AST-extracted `strip_comment()` from
`45085b33` gives the same expected first-hash removal required by the task's
legacy-compatibility criterion.

Required rework: track scalar/item-start state rather than inferring it solely
from the previous punctuation character. For a mapping value, determine quote
style from the first non-space value character. Within a flow list, reset item
start only after an actual flow comma. Do not let `-`, `,`, `[`, `{`, or `:`
appearing after already-consumed plain content reopen quote state. Add the two
counterexamples above to the root/template matrix.

### Remediation Validation Metrics

| Metric | Threshold | Measured value | Status |
| --- | --- | --- | --- |
| Requested remediation matrix | all pass in root/template | 9/9 | pass |
| Residual plain-scalar compatibility | all equal legacy behavior | 0/2 | **fail** |
| Focused regression suite | all tests pass | 16/16 | pass |
| Root/template AST parity | identical | identical | pass |
| Generated host lock | no drift | current | pass |
| Remediation scope | declared four targets only | 4/4, 0 extra | pass |
| Remediation diff hygiene | no whitespace errors | clean | pass |

### Remediation Commands and W4a Evidence

```text
python -m pytest tests/test_backlog_board_tasksets.py -q
16 passed in 1.83s

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --check 1c9ebc1c..09775885
pass

git diff --name-status 1c9ebc1c..09775885
M scripts/backlog_board.py
M src/agent_runtime/templates/project/scripts/backlog_board.py
M tests/fixtures/host/agent_runtime.lock.json
M tests/test_backlog_board_tasksets.py
```

The in-memory adversarial command imported both current parsers, AST-extracted
the legacy function from `45085b33`, ran the requested nine-case matrix, added
the two residual delimiter cases, compared root/template AST, and used PyYAML
only as a secondary semantic reference. It wrote no files.

The fresh W4a task and unit records parse correctly, identify worker
`codex-root-task-ar-608`, and each record 16 passing tests plus a current host
lock with return code zero and empty stderr:

- `reviews/VERIFY-2026-07-23-task-ar-608-20260723064403.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723064414.json`

### Final Remediation Verdict

**REJECT** TASK-AR-608 at W4a HEAD
`97b6bffa138de3b71117dd7b001e110eca825da5`, remediation implementation
`097758859e1f5f54655623fe077599718ec82292`.

The originally reported examples are closed, but the same quote-start
heuristic still suppresses valid plain-scalar comment boundaries after common
punctuation. The explicit acceptance criterion that unquoted comments retain
their prior behavior is therefore not yet satisfied.

This re-review modified only this skeptic report. It did not modify product
code, tests, task/unit metadata, runtime state, W4a evidence,
`reviews/INDEX.md`, or the separately present untracked W4b report.

## Final Scalar-State Re-review

This section records the final independent re-review of scalar-state
implementation `44d16a9abce8c539f812905b9c80f27cab147213` at W4a HEAD
`98498904008fc6876104053953d3e53c047e7098`. The two historical REJECT
sections and their exact counterexamples remain unchanged above. The
frontmatter now represents this final reviewed state and explicitly retains
both earlier rejected revisions.

### Findings

No blocking finding was reproduced at the final implementation SHA.

The new scanner replaces punctuation look-back with explicit state:

- `scalar_expected` distinguishes the start of a scalar/item from consumed
  plain content;
- `flow_stack` distinguishes top-level punctuation from list/map structure;
- `top_level_separator_seen` prevents a URL or later colon from reopening
  quote state; and
- quote close, flow comma, flow-map colon, and block bullet transitions update
  scalar state at their actual structural boundaries.

This closes both historical false-positive classes without adding a YAML
dependency or expanding the parser beyond the registered lexical subset.

### Independent Adversarial Matrix

Both root and host-template parsers produced the expected result for all 20
cases. Malformed cases were executed twice to confirm deterministic behavior.

| Boundary family | Cases | Result |
| --- | ---: | --- |
| plain scalar quote boundaries | mid single, mid double, `plain -`, top-level `plain,`, apostrophe | 5/5 pass |
| malformed plain/quoted input | unmatched mid quote, unterminated leading quote | 2/2 pass |
| colon context | URL/second colon, quoted mapping value, flow-map value colon | 3/3 pass |
| collection context | quoted bullet, flow-list comma, nested flow, two mismatched closers | 5/5 pass |
| quote escaping | escaped double quote, doubled single quote | 2/2 pass |
| legacy outside comment | ordinary unquoted comment | 1/1 pass |
| consumed-plain bracket guards | `plain [` and `plain {` before a quote | 2/2 pass |
| **Total** | **20** | **20/20 pass** |

Representative closures:

```text
plain - 'PR #167' # outside
=> "plain - 'PR " (trailing space)

plain, "PR #167" # outside
=> 'plain, "PR ' (trailing space)

summary: https://example.invalid:443 "PR #167" # outside
=> 'summary: https://example.invalid:443 "PR ' (trailing space)

meta: {label: "PR #167", note: 'issue #298'} # outside
=> preserves both quoted hashes and removes the outside comment
```

Leading quoted mapping values, block bullets, flow-list items, nested flow
values, escaped double quotes, YAML-style doubled single quotes, and quoted
hashes remain preserved. Unquoted and mid-plain hashes retain the legacy first-
hash removal behavior. Mismatched closers do not crash, do not diverge between
root/template, and remove the outside comment deterministically.

### Failure-First Provenance

Both registered failure-first stages are causal:

| Failure-first revision | Counterexample before fix | Final result |
| --- | --- | --- |
| `45085b33e0e29c48485edbc322b23026d0023c95` | leading `"PR #167 intact"` truncated to `"PR ` | preserved as `"PR #167 intact" ` |
| `7b50c8b1436b302d3ad37f113261de8a943aedb7` against `09775885` | `plain -` and top-level `plain,` retained inner hash | both remove from the first hash at `44d16a9a` |

The second failure-first commit changes only
`tests/test_backlog_board_tasksets.py` and precedes the scalar-state
implementation. AST-extracted functions from `45085b33`, `09775885`, and the
current worktree reproduced the failing-before/passing-after outputs without a
checkout or production-file mutation.

### Parity, Regression, Lock, and Scope Evidence

Root and template `strip_comment()` functions have identical normalized AST
with SHA-256:

```text
8a2b213aa51cb4ac187833aa65bf39e9ac80084e8be7fbecb2ea4ff1f767e3b9
```

Independent registered verification passed:

```text
python -m pytest tests/test_backlog_board_tasksets.py -q
16 passed in 1.11s

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --check 7b50c8b1..44d16a9a
pass

git diff --name-status 7b50c8b1..44d16a9a
M scripts/backlog_board.py
M src/agent_runtime/templates/project/scripts/backlog_board.py
M tests/fixtures/host/agent_runtime.lock.json
```

The implementation commit therefore changes only the two declared parser
copies and their generated host lock. The preceding failure-first commit owns
the two added assertions in the already-declared focused test file. No YAML
dependency, unrelated parser expansion, or out-of-scope product file appears.

The final W4a task and unit evidence records parse correctly, identify worker
`codex-root-task-ar-608`, and each contain 16 passing tests plus a current host
lock with zero return codes and empty stderr:

- `reviews/VERIFY-2026-07-23-task-ar-608-20260723064958.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723065008.json`

### Final Validation Metrics

| Metric | Threshold | Measured value | Status |
| --- | --- | --- | --- |
| adversarial scalar-state matrix | all cases pass in root/template | 20/20 | pass |
| malformed-input determinism | repeat output and parser parity | 4/4 checks | pass |
| first failure-first provenance | old fails, final passes | causal | pass |
| structural failure-first provenance | `09775885` fails, final passes | 2/2 causal | pass |
| root/template AST parity | identical | identical | pass |
| focused regression suite | all tests pass | 16/16 | pass |
| generated host lock | no drift | current | pass |
| implementation scope | declared parser pair plus lock only | 3 files, 0 extra | pass |
| diff hygiene | no whitespace errors | clean | pass |

### Final Verdict

**APPROVE** TASK-AR-608 at exact W4a HEAD
`98498904008fc6876104053953d3e53c047e7098`, implementation commit
`44d16a9abce8c539f812905b9c80f27cab147213`.

The scalar-state implementation closes both historical blockers, preserves the
original quoted-hash fix and unquoted-comment contract, maintains exact
root/template behavior, and passes the registered suite and generated lock
gate. The intentional residual boundary is the pre-existing hand-written YAML
subset; general YAML parsing remains out of scope by design.

This final re-review modified only this skeptic report. It did not modify
implementation files, tests, task/unit metadata, runtime state, W4a evidence,
or `reviews/INDEX.md`.
