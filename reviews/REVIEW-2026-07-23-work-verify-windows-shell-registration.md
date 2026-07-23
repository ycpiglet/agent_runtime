---
id: REVIEW-2026-07-23-work-verify-windows-shell-registration
title: Register Windows work-verify shell argument preservation defect
kind: planning
status: registered
date: 2026-07-23
owner: lead-engineer
---

# Windows work-verify shell argument preservation defect

## Current objective

Preserve verification command arguments exactly when `scripts/work.py verify`
runs on Windows, without expanding the scope of the active v0.7.0 release
closeout.

## Observed fact

The TASK-AR-602 W4a run recorded in
`reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202.json` passed the
full test suite (`2198 passed, 6 skipped`) but failed the tag peel command.
The declared `git rev-parse 'v0.7.0^{}'` reached Git with the caret/quote
sequence changed, because `_run_verification_command` delegates a command
string through `subprocess.run(..., shell=True)` and the Windows command shell
treats `^` as an escape character.

## Decision

- Register the runner defect as a separate initiative/taskset/task/unit before
  any implementation.
- Keep TASK-AR-602 scoped to release closeout. Replan its tag-target check to
  the shell-portable equivalent `git rev-parse v0.7.0~0`.
- Preserve the failed evidence file; it is part of the project history and is
  not overwritten by the passing rerun.

## Boundaries

- The follow-up owns `scripts/work.py` and focused work-verify tests.
- It must not alter release tags, GitHub releases, TASK-AR-602 release content,
  or historical evidence.
- The implementation must define and test the cross-platform command contract
  before changing process execution semantics.

## Next actions

1. Register the follow-up through `python scripts/work.py new` with a T0
   assumption snapshot.
2. Amend TASK-AR-602 task/unit verification metadata and body to use
   `git rev-parse v0.7.0~0`.
3. Rerun W4a and retain both failed and passing evidence references.

