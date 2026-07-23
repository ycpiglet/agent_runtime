---
title: TASK-AR-621 Skeptic and Adversarial Review
date: 2026-07-23
status: hold
signal: fail
score: 82
verdict: BLOCK
task_id: TASK-AR-621
unit_id: UNIT-TASK-AR-621-001
reviewed_head: 02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc
verified_by: /root/task_ar_611_auditor
worker: /root/task-ar-621
role: skeptic
tags:
  - task-ar-621
  - skeptic
  - windows
  - argv
  - frontmatter
  - compatibility
---

# TASK-AR-621 Skeptic and Adversarial Review

## Gate

This review evaluates the exact committed implementation at
`02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc` for independent W4b release from
the TASK-AR-621 claim. It checks the full registered-record-to-child-process
boundary, not only `_verification_argv()` in isolation.

Required properties were:

1. preserve caret and Windows backslashes;
2. remove single/double quote grouping delimiters while preserving grouped
   argument content;
3. retain stdout, stderr, return-code, and timeout evidence behavior;
4. remove implicit pipe, redirect, environment expansion, and chaining without
   breaking registered commands, while allowing an explicitly named shell.

## Readiness decision

**BLOCK — 82/100.**

The direct argv lexer and result envelope pass the isolated adversarial
probes. The release is blocked because a syntactically intended quote group in
a raw registered work record can be damaged by the existing frontmatter
parser, after which the new strict lexer refuses it before process launch.
The previous Windows `shell=True` path did launch the same parser-visible
command. This is an observed compatibility regression in the integrated
`work.py verify` input path, and one current `worker_ready` record has the
affected form.

## Blocking finding

### B1 — parser-to-lexer boundary rejects a currently registered terminal quote group

`scripts/backlog_board.py:574` parses a frontmatter list item with:

```python
item = raw_item.strip("'\"")
```

That operation does not distinguish an outer scalar quote from a quote that
terminates a command argument. For this valid raw record:

```yaml
verification:
  - python -c "print('legacy-ok')"
```

the execution pipeline observes:

```text
raw command:
python -c "print('legacy-ok')"

parser-visible command:
python -c "print('legacy-ok')
```

The independent Windows A/B result was:

```text
old subprocess.run(command, shell=True):
returncode=0
stdout="legacy-ok\n"

new _run_verification_command:
status=failed
returncode=2
stderr="No closing quotation"
child process not started
```

This is not merely a change in error wording. The old runner launched the
intended child successfully, while the new runner fails during
`list(shlex)`. A direct Windows string launch is also permissive to the end of
the command; the newly introduced strict tokenization is the point that turns
the pre-existing parser loss into a launch-blocking regression.

The repository contains the same form in the current worker-ready record:

```text
agents/lead_engineer/tasks/units/TASK-AR-586/UNIT-TASK-AR-586-002.md:37
python -c "import yaml; yaml.safe_load(open('.github/workflows/release-auto.yml'))"
```

Its raw text has balanced quotes. Its parser-visible verification command does
not, and the reviewed runner returns `failed`, return code 2, before Python can
execute it. The old shell path does execute Python; its later failure in this
checkout is an unrelated CP949 decode error while reading the target YAML.
That later target-command failure does not erase the launch compatibility
difference.

The focused tests create commands without a terminal quote group and therefore
do not exercise `raw frontmatter -> parse_frontmatter -> _verification_argv`.
The caret regression proves direct argument preservation but cannot catch this
integration failure.

TASK-AR-622 cannot presently absorb this as a nonblocking residual. Its
planner-approved acceptance and raw-record regression are explicitly limited
to an unquoted hash-bearing suffix. Neither its task nor unit requires
preserving a terminal single/double command quote. A future implementation
might incidentally fix the shared scalar parser, but intent or a broad title is
not sufficient W4b evidence for this concrete case.

## Passed adversarial checks

### Portable argv behavior

Independent vector checks passed for:

- unquoted, single-quoted, and double-quoted `v0.7.0^{}` caret arguments;
- quoted `C:\Program Files\...`, unquoted Windows paths, and UNC paths;
- single and double quote groups containing spaces;
- the opposite quote character inside a quote group;
- adjacent quote groups and empty quoted arguments;
- disabled `#` comments;
- literal `|`, `>`, `$HOME`, `%TEMP%`, and `&&` tokens;
- fail-closed unmatched quotes.

The child-process probe received these exact arguments:

```text
v0.7.0^{}
C:\Program Files\Tool
single group
left|right
$HOME
%TEMP%
```

This confirms that `posix=True`, `whitespace_split=True`, `commenters=""`, and
`escape=""` achieve the intended caret, grouping, and backslash behavior when
the input string reaches the lexer intact.

### Explicit-shell boundary

The default direct-argv path delivered pipe, redirect, and environment syntax
as literal child arguments rather than evaluating it. An explicit Windows
shell probe passed:

```text
cmd /d /s /c "echo explicit-shell|findstr explicit-shell"
```

The pipe ran only because `cmd` was named in the registered command. This is
compatible with the helper docstring's `cmd /c`, `powershell -Command`, and
`sh -c` contract.

### Evidence schema

Independent real-process probes confirmed the same seven command fields:

```text
command
status
returncode
started_at
finished_at
stdout
stderr
```

- nonzero child exit retained return code 7 plus both stdout and stderr;
- timeout retained `status=timeout`, `returncode=null`, and stdout emitted
  before timeout;
- lexer failure was normalized to failed/2 with the same field set;
- explicit-shell success retained normal passed/0 output.

The success, nonzero, and timeout envelope is therefore preserved. The blocker
is input compatibility before child launch, not evidence-shape corruption.

## Registered-command compatibility inventory

All machine-readable `verification` entries under
`agents/lead_engineer/tasks/**/*.md` were parsed with the production
frontmatter parser and then passed through the reviewed lexer:

```text
commands_total=293
implicit_shell_dependencies=0
lexer_errors=1
```

No registered command currently depends on implicit pipe, redirect, `&&`,
PowerShell/POSIX environment expansion, or CMD `%VAR%` expansion. Removing
those implicit features is therefore compatible with the otherwise parseable
registered corpus. The one error is the active TASK-AR-586 record described in
B1, so the inventory supports the blocker rather than reducing it to a
hypothetical external migration concern.

## Tests and gates

- `py -3.10 -m pytest tests/test_work_verify.py -q`:
  **8 passed in 4.64s**.
- `git diff --check main...HEAD`: pass.
- W4a evidence
  `reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106.json`
  records 8 focused tests and Owner governance passing at the reviewed commit.
- The literal `python -m pytest ...` command in this independent shell resolved
  to Python 3.14 without pytest; the repository verification runtime
  `py -3.10` was used for the independent focused run.
- The T3 plan-assumption check is red at the implementation HEAD because the
  recorded `scripts/work.py` anchor is the pre-implementation blob. The claim
  was already dispatched after T2, so this is not the compatibility blocker,
  but the T3 verification command cannot be reported green at this HEAD.
- An independent Owner-governance rerun reached the evidence-index gate and
  failed only because concurrently created, untracked TASK-AR-621 review files
  were not in `reviews/INDEX.md`. The preceding code and work-schema gates
  passed. A clean post-review governance rerun is still required before
  closeout.

## Warnings and residual risks

- At the exact committed HEAD, the explicit-shell contract is documented in a
  private helper docstring. The implementation-review document visible during
  W4b was untracked and is not part of the exact-HEAD evidence.
- The implementation intentionally normalizes missing-executable and lexer
  errors to return codes 127 and 2. The evidence schema is stable, but these
  values need not equal every former OS-shell-specific return code.
- With backslash escaping disabled, callers must use the opposite quote type or
  adjacent quote groups when an argument itself contains a quote delimiter.
  This limitation should be user-facing documentation, not only a code comment.
- The active claim and worktree remain expected W4/W5 state and are not
  themselves evidence of completed closeout.

## Required next actions

1. Add a full-path regression that starts from raw work frontmatter containing
   a verification command ending in a double-quoted group and proves the child
   receives the intended argv. Cover the equivalent single-quote boundary.
2. Fix the parser/serializer or execution boundary so terminal command-group
   quotes survive without restoring a global implicit shell. If TASK-AR-622 is
   chosen as owner, amend its planner-approved acceptance and raw-record tests
   to name this quote-loss case explicitly.
3. Add a focused explicit-shell regression for at least the Windows `cmd /c`
   contract and retain the direct literal-metacharacter assertion.
4. Commit and index the command-contract documentation, then rerun focused
   tests, the clean Owner-governance chain, and fresh W4a evidence at the
   repaired exact HEAD.
5. Request another independent exact-HEAD review before claim release.

## Final verdict

**Caret/backslash/quote lexer mechanics: PASS. Evidence envelope: PASS.
Registered-command integration compatibility: FAIL. TASK-AR-621: BLOCK.**
