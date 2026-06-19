---
title: Visual System Integration T3 Replan for TASK-AR-591
date: 2026-06-20
signal: pass
score: 92
tags: [work-replan, task-ar-591, ui-console, design-system]
---

# Visual System Integration T3 Replan for TASK-AR-591

## Bottom Line

T2 dispatch for `TASK-AR-591` correctly refused the claim because the taskset
registration review and `scripts/work.py` anchors drifted after the `TASK-AR-592`
closeout and upstream main integration. The original scope remains valid:
verify and complete the live wiring of the AR-587..590 visual components in the
served console without redesigning their component APIs.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | pass | `plan_assumption_gate` reported hash drift only; no missing anchor |
| Scope continuity | pass | `TASK-AR-591` still targets `ui_console_assets.py` and `ui_design_assets.py` wiring |
| Safety | pass | `footprint_conflict_gate` and `parallel_worktree_gate` passed before replan |

## Decision

Refresh the `TASKSET-AR-VISUAL-SYSTEM-INTEGRATION` plan assumptions against the
current repository state and continue with `TASK-AR-591` as the next UI work
unit. The implementation should first audit whether the prior `impl-task-ar-591`
code already satisfies the live wiring requirements; if yes, close the stale
task/unit records with evidence instead of inventing extra UI churn.

## Action Board

| Item | Action |
| --- | --- |
| `TASK-AR-591` | Claim `UNIT-TASK-AR-591-001`, audit live component usage, then fix only proven gaps |
| `TASK-AR-591` unit 2 | Boot-verify `/`, `/app.css`, `/app.js`, and served JS syntax |
| Governance | Re-run design-system, taskset, evidence, identity, and owner gates after closeout |

## Next

Re-record anchors:

- `reviews/REVIEW-2026-06-20-taskset-ar-visual-system-integration-registration.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`
