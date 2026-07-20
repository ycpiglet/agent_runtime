---
title: Hook Portability and Worktree Cleanup
date: 2026-07-20
signal: pass
score: 95
tags: [hooks, portability, git-hygiene, task-ar-601]
---

# Hook Portability and Worktree Cleanup

## Bottom Line

The Linux hook failures came from two independent repository-local defects:
the Codex hook manifest used Windows-only executable paths and `.cmd` files,
and the live Git hooks were tracked without executable bits while
`core.hooksPath` was unset. TASK-AR-601 replaces the manifest commands with
portable Python invocations, records executable Git hook modes, refreshes the
host lock, and applies the documented bootstrap configuration.

## Signal

| Check | Before | After |
| --- | --- | --- |
| Codex hook command paths | Windows absolute paths and `.cmd` dependencies | repository-relative `python` commands |
| Root Git hook mode | `100644` | `100755` |
| `core.hooksPath` | unset | `.githooks` |
| Focused regression | 4 expected RED failures | 37 tests passing |

## Insight

- The live and generated-host hook manifests are distinct product surfaces,
  but portability applies to both, so both manifests are covered by one
  parameterized regression.
- The Windows wrapper files remain available for explicit Windows workflows;
  the Codex manifests no longer require them.
- The first direct pre-commit execution exposed runtime SSoT drift after the
  platform error was removed: the generated wave/scout claims lacked the
  Owner-approved taskset transition and the board had not been regenerated.
  The orchestrator corrected those claim fields and regenerated the board in
  the main checkout. No dispatcher implementation was expanded in this unit.

## Decision

Use `python ...` in Codex hook manifests as the portable execution contract,
and treat executable Git index modes plus `core.hooksPath=.githooks` as separate
required conditions. Keep machine-specific interpreter discovery in optional
platform wrappers, not in the shared manifest.

## Verification

- The first independent W4b pass rejected the change because the dedicated
  update-notify test and two host-template documents still named the Windows
  wrapper. The correction updates those contracts to the portable module
  command and adds them to the unit's explicit target-file scope before W4 is
  rerun.
- The second independent W4b pass accepted commit `96e799d`: the expanded
  focused suite reported `56 passed`, the actual pre-commit hook exited 0,
  bootstrap was ready, and all 16 manifest commands were portable. Evidence:
  `reviews/W4B-2026-07-20-TASK-AR-601.md`.

- RED proof: four failures covering absolute Windows paths, `.cmd` use, dirty
  intake wiring, and non-executable root Git hooks.
- GREEN proof: `python -m pytest tests/test_stop_hook_owner_governance.py tests/test_session_dashboard.py tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`
  completed with `37 passed`.
- Direct hook proof: `./.githooks/pre-commit` started the full owner-governance
  chain; its remaining boundary/board findings were runtime SSoT findings, not
  process launch errors.
- Bootstrap proof: `python scripts/bootstrap_dev_env.py --apply` reported the
  editable checkout and `.githooks` wiring ready.

## Action

- Worker: keep the implementation limited to the declared TASK-AR-601 unit.
- Independent verifier: inspect the committed diff and rerun the recorded W4
  commands before claim release.
- Orchestrator: regenerate shared indexes, integrate serially, rerun the hook
  from main, and remove the task worktree and merged branch.

## Risks / Blockers

- `python` must remain available on `PATH`; the bootstrap command verifies this
  prerequisite.
- The existing HTTPS push transport warning is unchanged and out of scope.
- TASK-AR-600 references a missing `scripts/root_template_parity_gate.py`; that
  pre-existing verification-spec defect is recorded but not repaired here.

## Next

- Run W4a focused verification and record evidence.
- Obtain W4b approval from an independent agent instance.
- Integrate serially, rerun the real pre-commit hook from main, repoint the
  editable install to main, release the claim, and remove the task worktree and
  merged branch.
