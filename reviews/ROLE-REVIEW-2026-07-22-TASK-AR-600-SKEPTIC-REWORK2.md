---
title: TASK-AR-600 Skeptical High-Risk Rework 2 Review
date: 2026-07-22
signal: block
score: 90
tags: [task-ar-600, skeptic, auto-merge, rework2, external-effect]
---

# TASK-AR-600 skeptical high-risk rework 2 review

## Bottom line

**BLOCK.** Reviewed exact second-remediation HEAD
`c383302a8b8e5728019177b96cee5181915f9bad` in
`C:\Users\ycpig\agent_runtime\.worktrees\TASK-AR-600`.

The second remediation closes the PR-title/reason reserved-marker, CR/LF, ANSI,
quote, and backslash output-injection path. It also retains the prior fixes for
raw command output, secret-bearing exceptions, malformed payloads, validated
timestamps, Draft races, and command/read-back divergence. The focused suite
passes with `18 passed`.

One new high-risk external-effect blocker was confirmed at the command boundary:
the nominal PR positional argument is not validated and is placed before the
generated `gh` flags. A value such as `-Rattacker/other-repository` is accepted
by `main()` and forwarded unchanged to both `gh pr view` and `gh pr merge`.
`-R` is the GitHub CLI repository selector, so the argument is interpreted as
an option rather than a PR identifier. This can redirect lookup and merge
authority to another repository and leave `gh` to infer its current-branch PR.

No network, real `gh`, PR merge, branch operation, or external mutation was
performed. Exact subprocess argv was captured with in-process mocks only.

## Blocking finding

### High — option-like PR input can redirect the repository merge target

**Affected:** `auto_merge.py:61`, `auto_merge.py:164`, and
`auto_merge.py:208-212`.

Argument parsing removes only strings beginning with `--`; it accepts a
single-dash value as the first positional PR. Both GitHub commands then place
that value before their generated flags. The probe passed
`-Rattacker/other-repository` and captured:

```text
gh pr merge -Rattacker/other-repository --squash --delete-branch
gh pr view  -Rattacker/other-repository --json state,isDraft,mergedAt,mergeCommit
```

`main()` separately showed that the same value reached both `evaluate(pr)` and
`execute_merge(pr)`. List-form `subprocess.run` prevents shell metacharacter
execution, but it does not prevent the invoked CLI from parsing an attacker-
controlled argv element as its own option. Because this command can merge and
delete a branch, repository-target ambiguity is a blocking authorization flaw.

**Required remediation:** validate and normalize the PR identifier before the
first GitHub read. The safest current contract is an ASCII decimal PR number
matching `^[1-9][0-9]*$`; reject option-like, empty, signed, whitespace, branch,
and repository-selector inputs before invoking any subprocess. If full PR URLs
must be supported, parse them explicitly into an approved repository plus
number and enforce that repository against the configured current remote.
Additionally place generated options before a `--` positional separator if the
specific `gh` subcommands support it; do not rely on the separator alone as the
authorization check.

Add regressions proving `-Rowner/repo`, `-d`, `--repo`, shell metacharacters,
whitespace, Unicode digits, malformed URLs, and missing PR numbers cause a
controlled nonzero result with **zero** subprocess calls.

## Previous blockers rechecked

### Pass — reserved marker and terminal-control injection

PR identifier display, title, and reason strings pass through
`_safe_status_text`. A combined payload containing quotes, CR, LF, ANSI escape,
backslashes, and the exact `원격 MERGED 확인됨` marker produced four stable
output lines, no raw CR or ANSI, and no reserved success marker while read-back
failed. The marker was replaced by `[reserved-status-marker]`; quotes,
backslashes, and non-printable characters were rendered as text.

### Pass — command/read-back secret and status forgery

Both merge stdout and stderr contained a forged success marker, CR/LF, ANSI,
and secret sentinels. A remote `OPEN` payload also contained an extra secret
field. None appeared in CLI output. A secret-bearing `RuntimeError` from
read-back returned only its exception class. Controlled remote output retained
only the state enum and validated timestamp.

### Pass — malformed and divergent authoritative state

- Command exit `0` + remote `OPEN`: failure.
- Command exit `0` + `MERGED` with null timestamp: failure.
- Command exit `1` + valid remote `MERGED` timestamp: success, preserving the
  specified desired-state/concurrent-actor behavior.
- Non-object payload, boolean/unknown state, invalid calendar date, non-string
  and timezone-free timestamp: failure without payload propagation.
- Post-preflight Draft race: failure.
- Merge timeout plus non-merged read-back: failure with only the exception
  class; each subprocess receives a 30-second timeout.
- The reserved success marker is emitted by implementation status only after a
  true, validated `execute_merge()` result.

## Verification and probes

```powershell
git status --short
git rev-parse HEAD
git log --oneline --decorate -5
git diff b680fea40d934cdd7efb533301f945667bbced45..HEAD -- src/agent_runtime/templates/project/scripts/auto_merge.py tests/test_auto_merge_execution.py

$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;'+$env:PATH
python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
git diff --check
```

A corrected inline Python attack matrix loaded the exact module and mocked
`subprocess.run`, `gh_json`, `evaluate`, and `execute_merge`. It combined title,
reason, PR CLI input, command stdout/stderr, exceptions, and remote payloads;
captured exact argv; and exercised state/return-code/malformed/timestamp cases.
It did not execute `gh` or open a socket.

## Residual risks after the blocker is fixed

- The merge and read-back calls each have a 30-second timeout, so one attempt
  can take about 60 seconds. This is bounded but should remain an explicit
  automation latency budget.
- Single-shot read-back can return a safe false negative under eventual
  consistency. Any retry must be bounded and preserve ambiguous-as-failure.
- A valid remote `MERGED` can be caused by a concurrent actor after this command
  exits nonzero. Evidence should state that remote desired state was confirmed,
  not that this process caused the merge.
- Failed malformed timestamp output can contain the controlled word `MERGED` in
  `state=MERGED`; consumers must use exit status or a structured result rather
  than descriptive substring matching.
- `_safe_status_text` is an output-integrity transform, not a secrecy filter for
  intentionally public PR titles/reasons. Operators must not put credentials in
  PR metadata.

## Approval condition

Reject or safely normalize option-like/cross-repository PR input before any
subprocess call, add zero-call adversarial tests, and rerun this review on the
new exact HEAD. Until then, the verdict remains **BLOCK**.
