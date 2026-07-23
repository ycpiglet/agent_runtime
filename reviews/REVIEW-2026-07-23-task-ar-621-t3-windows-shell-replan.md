---
id: REVIEW-2026-07-23-task-ar-621-t3-windows-shell-replan
title: TASK-AR-621 T3 Windows verification shell replan and re-anchor
kind: planning
status: approved
date: 2026-07-23
task_id: TASK-AR-621
task_set_id: TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY
decision: replan
---

# TASK-AR-621 T3 Windows verification shell replan and re-anchor

## Current objective

Make TASK-AR-621 dispatch-ready and preserve registered verification command
arguments on Windows without changing the verification evidence schema or
rewriting historical evidence.

## Drift finding

The T2 check found only the registration review anchor changed. The automatic
T0 digest was recorded against the review's pre-commit working-tree bytes,
while the committed checkout contains the normalized LF bytes. The design
decision, target files, acceptance criteria, and runner implementation have
not changed since registration.

## T3 decision

- Re-anchor the taskset from this T3 record and current committed dispatcher
  and verification-runner bytes.
- Define the Windows command execution contract in a regression test before
  changing the runner.
- Preserve shell features used by registered verification commands while
  preventing the Windows command processor from consuming metacharacters
  inside quoted arguments.
- Keep result status, exit code, stdout, stderr, duration, and timeout evidence
  compatible with `agent-runtime-work-verification/v1`.
- Do not modify existing verification evidence or introduce a new source of
  untrusted commands.

## Re-anchor set

- `reviews/REVIEW-2026-07-23-task-ar-621-t3-windows-shell-replan.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`

## Verification

- `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY`
- `python -m pytest tests/test_work_verify.py -q`
- `python scripts/owner_governance_gate.py`
