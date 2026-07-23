---
status: complete
origin_type: task_closeout
origin_ref: agents/lead_engineer/tasks/TASK-AR-621.md
tags:
  - task-ar-621
  - work-cli
  - windows
  - verification
  - closeout
---

# TASK-AR-621 Closeout

## Outcome

`TASK-AR-621` and `TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY` are complete.
On Windows, verification commands now bypass implicit `cmd.exe` interpretation
while preserving native Windows command-line parsing and compatibility with the
registered legacy terminal-quote form. POSIX keeps the existing shell contract.

## Verification Chain

- Failure-first commit `c06615ff` reproduced caret loss through the real
  `work.py verify` path.
- The first portable-lexer fix was rejected after skeptical review proved that
  a real registered legacy command depended on native Windows terminal-quote
  handling.
- Reworked implementation commit `0b5da107` sends the original command string
  to `subprocess.run(..., shell=False)` on Windows and retains `shell=True` on
  POSIX. An `OSError` becomes the existing failed verification envelope with
  return code 127.
- Final focused verification passed all 9 tests in `tests/test_work_verify.py`.
- Task and unit W4a evidence passed; independent W4b recheck scored 99 and
  skeptic recheck scored 97 with no blockers.
- The exact independently reviewed code/evidence head was
  `c27d3706536bc5e70b58a1d35c4644462ece5199`.

## Integration Evidence

- Pull request: #344
- PR head: `59d73130ffc3226cb66a6079e2f57d4da30c9313`
- Merge commit: `c600bf1cbaafe6319529b7126574ae1316f73984`
- Pull-request CI run: `29988050884` — Python 3.10, 3.11, and 3.12 passed.
- Post-merge main CI run: `29988207028` — Python 3.10, 3.11, and 3.12 passed.
- Release evidence:
  `reviews/W4B-2026-07-23-TASK-AR-621-RELEASE.md`

## Scope Boundary

Commands that intentionally require Windows shell features must invoke an
explicit shell such as `cmd /c` or `powershell -Command`. No registered
verification command required an implicit Windows shell at closeout.

## Next Work

Resume worker-ready `TASK-AR-622` in
`TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY` through a fresh W0~W6 lifecycle.
