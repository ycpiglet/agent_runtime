---
title: TASK-AR-600 Skeptical High-Risk Rework 3 Review
date: 2026-07-22
signal: pass
score: 98
tags: [task-ar-600, skeptic, auto-merge, rework3, external-effect]
---

# TASK-AR-600 skeptical high-risk rework 3 review

## Bottom line

**APPROVE.** Reviewed exact third-remediation HEAD
`fe26bed19442ad1ff2d32e1f4ebf0c98b68cd496` in
`C:\Users\ycpig\agent_runtime\.worktrees\TASK-AR-600`.

The PR option-injection blocker is closed at all three entry points. `main()`,
`execute_merge()`, and `gh_json()` accept only a nonzero ASCII decimal PR
number. An independent matrix of 23 malformed/option-like values made zero
subprocess calls; `main()` also made zero evaluation calls. A valid `123` was
forwarded as one positional argv element to the expected repository-local
`gh pr view` and `gh pr merge` commands.

All earlier blockers remain closed: authoritative state and timestamp are
validated, command/read-back secrets are not reflected, malformed payloads and
exceptions fail closed, untrusted status text cannot forge the reserved success
marker or inject terminal controls, and the success marker is emitted only on a
validated true result. The focused suite passes with `21 passed`.

No network, real `gh`, PR merge, branch operation, or external mutation was
performed. Every command and response was replaced with an in-process mock.

## PR input boundary

### Invalid input — pass with zero external calls

The independent matrix included:

- `-Rattacker/other-repository`, `-d`, and `--repo owner/repo`
- empty input, missing input, and extra positional arguments
- `+1`, `-1`, `0`, and leading-zero `01`
- leading/trailing/tab whitespace
- full-width and Arabic Unicode digits
- a GitHub PR URL
- semicolon, pipe, command-substitution, and backtick shell/meta strings
- embedded newline and NUL values
- direct non-string `None` and integer values

For `main()`, all 23 argv cases returned usage error `2`, made zero calls to
`evaluate`, and made zero subprocess calls. For direct `execute_merge()` and
`gh_json()`, all 23 values returned or raised the controlled
`PR 번호 형식 오류` result and made zero subprocess calls. Shell
metacharacters therefore never reached either a shell or the GitHub CLI.

### Valid input — pass with exact argv

For PR number `123`, captured commands were exactly:

```text
gh pr view  123 --json state
gh pr merge 123 --squash --delete-branch
gh pr view  123 --json state,isDraft,mergedAt,mergeCommit
```

Each real command construction used list-form subprocess argv and a 30-second
timeout. `main()` passed normalized string `123` to both `evaluate` and
`execute_merge`.

## Previous blockers rechecked

### Authoritative success/failure boundary — pass

- Command exit `0` + remote `OPEN`: non-success.
- Command exit `0` + `MERGED` with null/invalid timestamp: non-success.
- Command exit `1` + validated remote `MERGED` timestamp: success, preserving
  the approved desired-state/concurrent-actor behavior.
- Draft race, invalid state, non-object payload, malformed JSON, invalid
  calendar date, boolean/list/non-timezone timestamp, and read-back exception:
  non-success.
- A valid timezone-aware `MERGED` result emitted the reserved marker and exit
  `0`; every attacked false case omitted the marker and returned nonzero.

### Output integrity and secret containment — pass

A combined title/reason payload contained the reserved marker, quotes, CR/LF,
ANSI, backslashes, and escaped-line text. Output retained stable line structure,
contained no raw controls, and replaced the reserved phrase. Merge stdout,
stderr, exception messages, and extra remote payload fields contained distinct
secret sentinels and a forged success marker; none reached returned or printed
status. Only controlled exception classes, state enums, return codes, and a
validated timestamp are exposed.

### Dry-run, `SKIP`, and policy behavior — pass

The earlier independent passes for dry-run and `SKIP` remain covered by the
unchanged execution flow and focused suite. Invalid input is rejected before
evaluation, so it cannot obtain `SKIP`, `ESCALATE`, or merge behavior through
an option-parsing ambiguity.

## Verification and attack probes

```powershell
git status --short
git rev-parse HEAD
git log --oneline --decorate -5
git diff c383302a8b8e5728019177b96cee5181915f9bad..HEAD -- src/agent_runtime/templates/project/scripts/auto_merge.py tests/test_auto_merge_execution.py

$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;'+$env:PATH
python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
git diff --check
```

An independent inline Python probe loaded the exact module and instrumented
`subprocess.run`, `evaluate`, `execute_merge`, and `gh_json`. It asserted zero
calls for all invalid main/direct cases, captured exact valid argv and timeout,
and reattacked return-code divergence, malformed state/timestamps, exceptions,
secret-bearing command/payload data, control characters, and true/false marker
boundaries. All assertions passed without invoking `gh` or opening a socket.

## Residual non-blocking risks

- The ASCII numeric validator has no explicit digit-count cap. An extremely
  large locally supplied number can cause bounded local argument-processing or
  OS command-line failure, but it cannot become a CLI option or redirect the
  repository. A practical length cap would improve denial-of-service hygiene.
- The merge and read-back calls each have a 30-second timeout, so one attempt
  can consume about 60 seconds. This is bounded and should remain an explicit
  automation latency budget.
- Single-shot read-back can produce a safe false negative under eventual
  consistency. Any retry must remain bounded and preserve ambiguous-as-failure.
- A valid remote `MERGED` can come from a concurrent actor after this command
  exits nonzero. Evidence should describe confirmed remote desired state, not
  command causation.
- `SKIP` retains exit `0`; callers must distinguish no-op from actual merge by
  verdict or structured evidence rather than exit status alone.

## Verdict

The high-risk skeptic gate for TASK-AR-600 is **APPROVE** at exact HEAD
`fe26bed19442ad1ff2d32e1f4ebf0c98b68cd496`.
