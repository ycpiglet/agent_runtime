---
title: Stop Hook Session Scope Quoted Payload Guard
date: 2026-06-18
signal: pass
score: 100
tags: [stop-hook, dirty-intake, session-scope, windows]
---

# Stop Hook Session Scope Quoted Payload Guard

## Bottom Line

Stop hook output is valid in the three registered Stop hooks, and the session
scope parser now ignores repo paths embedded inside PowerShell assignment
strings. This prevents a reproduction payload or temp-file setup command from
being misread as work on an unrelated dirty repo file.

## Signal

| Check | Result |
| --- | --- |
| question-only Stop hook outputs | pass, 0-byte stdout for owner, dirty, closure |
| mutating dirty-intake block output | pass, valid Stop JSON |
| quoted payload reproduction | pass, 0-byte stdout |
| hook tests | pass, 31 tests |
| owner governance | pass |

## Decision

Mask PowerShell assignment RHS text before extracting touched paths from shell
commands. Keep variable resolution from the original command so real commands
like `$target='scripts/current.py'; Set-Content -LiteralPath $target ...` still
count as touching the repo path.

## Scope

- Updated `scripts/stop_hook_session_scope.py`.
- Mirrored the helper to the host-project template copy.
- Added a regression test for embedded command strings that mention dirty repo
paths but only write a temp transcript.
- Regenerated the host lock fixture.

## Residual State

Existing unrelated dirty files remain untouched:

- `ARCHIVE-INDEX.md`
- `agents/runtime/session_baselines/session-baseline-2026-06-18T*.json`
- `reviews/PATCH-2026-06-18-design-gate-entity-fp.diff`
