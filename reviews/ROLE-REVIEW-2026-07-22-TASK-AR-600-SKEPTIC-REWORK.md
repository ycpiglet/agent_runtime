---
title: TASK-AR-600 Skeptical High-Risk Rework Review
date: 2026-07-22
signal: block
score: 86
tags: [task-ar-600, skeptic, auto-merge, rework, external-effect]
---

# TASK-AR-600 skeptical high-risk rework review

## Bottom line

**BLOCK.** Reviewed exact rework HEAD
`b680fea40d934cdd7efb533301f945667bbced45` in
`C:\Users\ycpig\agent_runtime\.worktrees\TASK-AR-600`.

The rework resolves the original raw command-output path, secret disclosure,
and malformed authoritative-read-back handling. The focused suite passes with
`17 passed`, and independent probes confirmed that return-code divergence,
Draft racing, timeout, malformed payloads, and exception messages fail safely.

One status-output injection path remains: the remote PR title is printed without
escaping before merge execution. A title containing the exact
`원격 MERGED 확인됨` marker makes that marker appear in CLI output even when
read-back is `OPEN`, the command result is unconfirmed, and `main()` returns
`1`. This preserves the human/naive-parser false-success ambiguity that the
first blocking finding required the CLI boundary to remove.

No network call, real `gh` invocation, PR merge, branch update, or other
external change occurred. All subprocess and GitHub responses were mocked in
process.

## Original blocking findings rechecked

### 1. Partial pass — raw merge output is contained, but another untrusted status field can forge the marker

**Raw command output:** fixed. `execute_merge()` no longer returns or prints
stdout/stderr. A mock placed `원격 MERGED 확인됨`, `CMD_SECRET`, and
`ERR_SECRET` in both streams while remote state was `OPEN`; CLI exit was `1`,
and none of those strings appeared from the command output.

**Remaining blocker:** `auto_merge.py:198` interpolates
`d.get('title', '')[:50]` directly into the status line. With the mocked title
`원격 MERGED 확인됨` and a failed `OPEN` read-back, output was:

```text
[auto_merge] PR #123 "원격 MERGED 확인됨" → AUTO-MERGE
  - green
원격 머지 확인 실패: state=OPEN, mergedAt=invalid; merge exit=0
  → 머지 미확정: 원격 PR이 MERGED가 아니므로 실패 처리.
```

The return code is correctly nonzero, but the exact authoritative success
marker remains present in a remotely controlled field. Quotes are not a safe
machine boundary, and the same interpolation also permits terminal-control or
line-structure ambiguity if such characters reach the API payload.

**Required remediation:** either omit the PR title from merge status output or
render all remote strings through a strict single-line escaping function that
also prevents reserved agent-runtime status phrases/control characters from
appearing verbatim. Prefer a structured status token independent of descriptive
text. Add a CLI-level test with a forged marker, quotes, carriage return/newline,
and ANSI escape bytes in the title, and assert that a failed read-back cannot
emit the reserved success marker or alter line structure.

### 2. Pass — merge/read-back secrets are sanitized

Command stdout/stderr is discarded from status. `gh_json()` reports only the
exit code or exception class, and `execute_merge()` reports only controlled
state, return code, or exception class. Independent sentinels in merge stdout,
merge stderr, a `SystemExit`, `JSONDecodeError`, `RuntimeError`, remote extra
fields, and timeout payloads did not appear in returned or printed diagnostics.

### 3. Pass — malformed read-back fails closed

The following independent cases returned non-success without propagating a
payload error: invalid JSON, read-back exceptions, null/list payloads, boolean
or unknown state, missing `mergedAt`, boolean/list/non-timestamp/no-timezone/
invalid-date `mergedAt`. Valid timezone-aware `Z` and `+09:00` timestamps were
accepted only with exact `state=MERGED`. The returned remote object is reduced
to controlled state and validated timestamp fields, so extra remote secrets are
not reflected.

## Other adversarial results

- Command exit `0` + remote `OPEN`: failure.
- Command exit `0` + `MERGED` but null timestamp: failure.
- Command exit `1` + valid remote `MERGED`: success, preserving the intended
  local-cleanup/concurrent-actor policy.
- Post-preflight Draft race (`OPEN`, `isDraft=true`): failure.
- Merge `TimeoutExpired` + remote `OPEN`: failure with only the exception class.
- Both merge and read-back subprocess calls receive a `30` second timeout.
- Dry-run `AUTO-MERGE` and `SKIP` did not invoke `execute_merge`; `SKIP` retains
  exit `0`.
- Existing focused suite: `17 passed in 0.21s`.
- `git diff --check` passed and the implementation worktree was clean.

## Commands and mocked probes

```powershell
git status --short
git rev-parse HEAD
git log --oneline --decorate -6
git diff 070c05b3df1a35336546a375b739af4892066769..HEAD -- src/agent_runtime/templates/project/scripts/auto_merge.py tests/test_auto_merge_execution.py

$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;'+$env:PATH
python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
git diff --check
```

An inline Python matrix loaded the exact module and replaced `subprocess.run`,
`gh_json`, `evaluate`, and `execute_merge` as appropriate. It exercised the
return-code/state cross-product, Draft race, timeouts, exceptions, malformed
types and timestamps, raw-output sentinels, concurrent merge state, dry-run,
`SKIP`, and the PR-title marker injection. It did not invoke `gh` or open a
socket.

## Residual risks after the blocker is fixed

- The two sequential `gh` operations each have a 30-second timeout, so a fully
  timed-out attempt can still block for about 60 seconds. This is bounded but
  should be an explicit automation latency budget.
- Single-shot read-back can produce a safe false negative under eventual
  consistency. Any retry must be bounded and must preserve ambiguous-as-failure.
- A valid remote `MERGED` state can be caused by a concurrent actor even when
  this command exits nonzero. This is consistent with the design's desired-state
  policy, but evidence should say “remote state confirmed,” not claim that this
  process caused the merge.
- `state=MERGED, mergedAt=invalid` is correctly a failure, but the diagnostic
  still contains the word `MERGED`. Consumers must use exit status or a future
  structured result, not substring matching on descriptive diagnostics.

## Approval condition

Remove or safely encode the untrusted PR-title status field and add the
CLI-level reserved-marker/control-character regression. Then rerun the skeptic
review on the new exact HEAD. Until then, the verdict remains **BLOCK**.
