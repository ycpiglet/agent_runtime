---
title: Visual Asset Adoption T3 Replan
date: 2026-06-20
signal: pass
score: 90
tags: [replan, t3, visual-asset-adoption, ui-ux]
---

# Visual Asset Adoption T3 Replan

## Bottom Line

`TASKSET-AR-VISUAL-ASSET-ADOPTION` remains valid for the current UI/UX
refactor cycle. The T2 dispatch check found anchor drift in the registration
review and `scripts/work.py`, so dispatch must re-anchor before claiming
`TASK-AR-588`.

## Drift Review

| Anchor | Finding | Decision |
| --- | --- | --- |
| `reviews/REVIEW-2026-06-20-taskset-ar-visual-asset-adoption-registration.md` | hash changed | Accept current file as the refreshed planning record. |
| `scripts/work.py` | hash changed | Accept current dispatcher/workflow implementation; no scope change required. |
| `scripts/task_claim_dispatcher.py` | unchanged | Keep claim-first dispatch semantics. |

## Scope Decision

Continue with `TASK-AR-588` as the next source-mutating UI task in the current
checkout. The active goal still needs concrete visual-system progress, and
`TASK-AR-588` directly advances graph layout, status encoding, motion-ready
SVG structure, and self-hosted visual assets.

## Claim Boundary

- Claim `TASK-AR-588` / `UNIT-TASK-AR-588-001` first.
- Keep work in a dispatcher-created worktree.
- Target only the declared graph asset files for this unit:
  `src/agent_runtime/ui_console_assets.py`,
  `src/agent_runtime/ui_design_assets.py`, and `tests/test_ui_console.py`.
- Do not mutate adjacent visual asset tasks (`TASK-AR-589` or `TASK-AR-590`)
  without a separate claim.

## Verification Before Dispatch

After this replan, refresh the T0/T3 assumption snapshot for
`TASKSET-AR-VISUAL-ASSET-ADOPTION` with the current registration review,
`scripts/task_claim_dispatcher.py`, and `scripts/work.py`; then rerun
`plan_assumption_gate --check --taskset TASKSET-AR-VISUAL-ASSET-ADOPTION`.
