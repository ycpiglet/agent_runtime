---
title: TASK-AR-621 Skeptic Recheck
date: 2026-07-23
status: approved
signal: pass
score: 97
verdict: APPROVE
task_id: TASK-AR-621
unit_id: UNIT-TASK-AR-621-001
reviewed_head: c27d3706536bc5e70b58a1d35c4644462ece5199
previous_review: reviews/ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC.md
verified_by: /root/task_ar_611_auditor
worker: /root/task-ar-621
role: skeptic
tags:
  - task-ar-621
  - skeptic
  - recheck
  - windows
  - subprocess
  - compatibility
---

# TASK-AR-621 Skeptic Recheck

## Gate

This addendum rechecks the exact committed HEAD
`c27d3706536bc5e70b58a1d35c4644462ece5199` after the BLOCK at
`02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc`. It evaluates:

1. the parser-visible terminal-quote compatibility counterexample;
2. Windows caret and native quoting/backslash preservation;
3. retention of the previous POSIX shell contract;
4. the Windows implicit/explicit shell-operator boundary;
5. stdout, stderr, return-code, launch-error, and timeout evidence.

## Readiness decision

**APPROVE — 97/100.**

The previous blocker is resolved. On Windows, the revised runner passes the
parser-visible command string directly to `CreateProcess` through
`subprocess.run(..., shell=False)`. This preserves native permissive
end-of-command quoting while preventing `cmd.exe` from consuming the caret.
On POSIX, the runner still selects `shell=True`, retaining the original command
contract rather than imposing the rejected cross-platform lexer.

No blocking finding remains at the reviewed HEAD. Approval authorizes claim
release and normal W5/W6 integration after the review/index bookkeeping is
committed and governance is clean; it does not claim that cleanup is already
complete.

## Previous blocker disposition

### Raw terminal-quote A/B

The exact prior counterexample was recreated from raw frontmatter:

```yaml
verification:
  - python -c "print('legacy-ok')"
```

The existing parser still exposes:

```text
python -c "print('legacy-ok')
```

Independent Windows execution produced:

| Runner | Child launched | Return code | stdout |
| --- | --- | --- | --- |
| previous `shell=True` | yes | 0 | `legacy-ok` |
| revised string + `shell=False` | yes | 0 | `legacy-ok` |

The revised runner returned a normal seven-field passed result instead of the
first implementation's `No closing quotation`/2 pre-launch failure.

The real current `worker_ready` record
`agents/lead_engineer/tasks/units/TASK-AR-586/UNIT-TASK-AR-586-002.md` was also
replayed through both paths. Both launched Python and reached the same later
CP949 decode failure:

```text
old shell path: returncode 1, Python traceback
new direct path: returncode 1, Python traceback
```

That target-file decoding defect is pre-existing and outside TASK-AR-621. The
compatibility property at issue here—reaching the intended child process—is
restored.

**Blocker disposition: RESOLVED.**

## Adversarial execution checks

### Windows caret, path, quote, and operator literals

A real child process in a temporary directory with spaces observed these exact
arguments from the revised runner:

```text
v0.7.0^{}
C:\Program Files\Agent Runtime\check.py
group with spaces
left|right
>audit.txt
%TEMP%
$HOME
a&&b
```

No redirect file was created, and the environment markers were not expanded.
The same caret command through the previous implicit Windows shell reached the
child as `v0.7.0{}`; the revised path delivered `v0.7.0^{}`. The original defect
is therefore fixed at the real child argv boundary.

Native Windows double-quote grouping and backslashes are preserved. Windows
single quotes are not newly promoted to grouping syntax, which matches the
previous CMD/Windows command-line contract rather than introducing a new
portable grammar.

### Explicit Windows shell

The default runner left shell operators literal. Explicit opt-in checks passed:

```text
cmd /d /s /c "echo explicit-shell|findstr explicit-shell"
```

- pipe executed;
- status passed, return code 0;
- stdout contained `explicit-shell`.

An explicit CMD redirect plus `%TEMP%` expansion created the expected temporary
file with an expanded value. An explicit PowerShell command also passed and
expanded `$env:TEMP`:

```text
powershell -NoProfile -Command "Write-Output ('explicit-powershell-' + $env:TEMP)"
```

This supports the committed contract: ordinary Windows verification commands
do not receive implicit shell semantics, while records that name `cmd /c` or
`powershell -Command` retain those semantics.

### POSIX contract

`_verification_uses_shell()` returns false for `win32` and true for a POSIX
platform value. With the subprocess call mocked only to observe the boundary,
`_run_verification_command(..., "printf ok | cat", ...)` passed
`shell=True` on the POSIX branch and `shell=False` on the Windows branch.

The relevant POSIX execution line is otherwise the same original
`subprocess.run(command, shell=True, ...)` contract. No lexer or argv
translation remains on that branch.

### Evidence behavior

Independent real-process checks retained the command-result field set:

```text
command
status
returncode
started_at
finished_at
stdout
stderr
```

- nonzero child exit: failed, exact return code 7, stdout and stderr retained;
- timeout: `status=timeout`, `returncode=null`, pre-timeout stdout retained;
- missing executable: failed, return code 127, seven fields retained;
- terminal-quote success: passed, return code 0, stdout retained;
- explicit-shell success: passed, return code 0, stdout retained.

The `agent-runtime-work-verification/v1` envelope and the per-command schema
are unchanged.

## Registered-command compatibility inventory

The canonical task/unit frontmatter inventory was rescanned:

```text
commands_total=293
implicit_shell_dependencies=0
batch_entrypoints=0
first tokens: python=276, pytest=11, git=6
```

No current registered command depends on implicit Windows pipe, redirect,
environment expansion, or command chaining. The known terminal-quote record
now executes through the direct Windows path, so the prior inventory exception
is no longer a runner failure.

## Tests and gates

- `py -3.10 -m pytest tests/test_work_verify.py -q`:
  **9 passed in 4.98s**.
- The added Windows regression traverses raw work frontmatter and asserts that
  the parser-visible terminal-quote command launches, returns 0, and emits
  `legacy-ok`.
- `git diff --check
  02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc..HEAD`: pass.
- Fresh W4a evidence
  `reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351.json`
  records 9 focused tests and Owner governance passing at the reworked commit.
- The committed implementation review now documents the Windows direct-string,
  POSIX shell-preserving, and explicit Windows shell contracts.

An independent Owner-governance run during this recheck reached
`evidence_index_generator.py` and failed only because a concurrently created,
untracked `reviews/W4B-2026-07-23-TASK-AR-621-RECHECK.md` was not yet in
`reviews/INDEX.md`. All preceding code, schema, taskset, identity, and
classifier gates passed. This is review closeout bookkeeping rather than a
failure at the exact code HEAD, but governance must be rerun after all review
files are committed and the index is regenerated.

## Blockers

None.

## Warnings and residual risks

- The POSIX branch was verified by exact code comparison and a mocked platform
  boundary from this Windows host, not by launching a real POSIX shell. Its
  `shell=True` behavior is unchanged from the pre-task runner.
- Windows batch entrypoints can have OS-specific launch behavior beyond normal
  executable command lines. The canonical inventory contains no `.bat` or
  `.cmd` verification entry; future records should use an explicit reviewed
  shell when shell semantics are required.
- The platform contract is intentionally not one portable quoting grammar:
  Windows uses native command-line parsing and POSIX uses its shell. This is
  the compatibility-preserving design decision and should remain visible in
  user-facing command authoring guidance.
- The updated unit file has no terminal newline. This is non-semantic and
  `git diff --check` passes, but it can be normalized during serial integration
  if doing so does not disturb evidence bookkeeping.
- TASK-AR-586's YAML CP949 decode failure remains an unrelated issue in that
  record's target command. TASK-AR-621 neither creates nor masks it.

## Required next actions

1. Commit and index this skeptical recheck together with the concurrent W4b
   recheck record.
2. Regenerate `reviews/INDEX.md` and rerun Owner governance cleanly.
3. Release the TASK-AR-621 claim with the fresh independent evidence.
4. Complete serial W5/W6 integration, worktree cleanup, and a fresh W0
   divergence check.

## Final verdict

**Previous terminal-quote blocker: RESOLVED. Caret and Windows operator
boundary: PASS. POSIX contract retention: PASS. Evidence compatibility: PASS.
TASK-AR-621: APPROVE.**
