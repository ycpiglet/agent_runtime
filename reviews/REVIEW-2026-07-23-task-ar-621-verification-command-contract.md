---
id: REVIEW-2026-07-23-task-ar-621-verification-command-contract
title: TASK-AR-621 portable verification command execution contract
kind: implementation-review
status: w4a_verified
date: 2026-07-23
task_id: TASK-AR-621
task_set_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
---

# TASK-AR-621 portable verification command execution contract

## Current objective

Prevent the operating-system shell from silently changing arguments in
registered `work.py verify` commands while retaining the existing verification
result and evidence behavior.

## Failure-first evidence

At commit `c06615ff`, the Windows regression invoked a child with the registered
argument `v0.7.0^{}` through the existing `shell=True` runner. The child
reported `v0.7.0{}`, proving that `cmd.exe` consumed the caret before process
startup. The companion timeout test passed against the old runner, establishing
the evidence compatibility baseline.

## Execution contract

The first implementation at `fcc6121f` tokenized every command into a portable
argv. Independent skeptical review found that this broke one real
`worker_ready` record whose terminal double quote is removed by the existing
frontmatter parser even though Windows previously executed the parser-visible
command.

The revised contract therefore changes only the platform boundary that caused
the defect:

- Windows passes the registered command line directly to `CreateProcess` with
  `shell=False`, so `cmd.exe` cannot consume carets or other metacharacters;
- native Windows double-quote and backslash behavior remains unchanged,
  including compatibility with the known terminal-quote legacy record;
- POSIX retains its existing `shell=True` command contract;
- a Windows command that intentionally needs a shell builtin or operator must
  name `cmd /c` or `powershell -Command` explicitly.

This is narrower than replacing command syntax for every host and preserves the
existing parser-visible command behavior while removing the Windows command
processor from ordinary verification execution.

## Compatibility

The `agent-runtime-work-verification/v1` envelope and per-command fields are
unchanged. Existing tests verify:

- successful exit with captured stdout;
- nonzero exit with the exact return code plus stdout and stderr;
- timeout with `returncode: null` and the same seven result fields;
- Windows caret preservation through the full `work.py verify` path;
- execution of the known Windows legacy terminal-quote command shape;
- quoted scalar/list preservation already covered by the work lifecycle tests.

Windows process-launch failures now produce a normal failed command result with
return code `127` and the existing field set instead of escaping the
verification workflow as an unhandled exception.

## Residual boundary

Implicit Windows pipe, redirect, environment expansion, builtins, and command
chaining are unavailable because `cmd.exe` is no longer implicit. The
repository-wide inventory found no registered verification command that
depends on those features; future Windows records must opt into an explicit
shell. POSIX shell behavior is unchanged.

TASK-AR-621 does not change work-item parsing. General lossless frontmatter
scalar handling remains separately registered as TASK-AR-622.

## Verification

- failure-first: `c06615ff`, caret regression failed as expected
- first W4a: `02e111e1`, `8 passed`
- first skeptical W4b: blocked on the real terminal-quote compatibility case
- compatibility rework: `0b5da107`
- revised focused run: `9 passed`, including that exact legacy shape
- revised W4a:
  `reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351.json`
- a fresh W4b is required on the follow-up exact HEAD before closeout
