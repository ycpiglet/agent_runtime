---
title: Visual Asset Adoption T3 Replan for TASK-AR-587
date: 2026-06-20
signal: pass
score: 92
tags: [work-replan, task-ar-587, ui-console, design-system]
---

# Visual Asset Adoption T3 Replan for TASK-AR-587

## Bottom Line

T2 dispatch for `TASK-AR-587` correctly refused the claim because the taskset
registration review and `scripts/work.py` anchors drifted after related visual
system integration work. The original taskset remains valid, but `TASK-AR-587`
must be handled evidence-first: audit the avatar implementation that already
appears in the executable UI asset layer, close proven requirements with fresh
verification, and fill only concrete gaps.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Drift type | pass | `plan_assumption_gate` reported hash drift only; no missing anchor |
| Scope continuity | pass | `TASK-AR-587` still targets deterministic self-hosted agent avatars and role accents |
| Integration continuity | pass | `TASK-AR-591` and `TASK-AR-592` already verified live visual wiring and responsive/a11y passes |
| Safety | pass | W0 reported `active_claims=0`; no existing claim owns this task |

## Decision

Refresh the `TASKSET-AR-VISUAL-ASSET-ADOPTION` plan assumptions against the
current repository state and continue with `TASK-AR-587` as the next UI/UX
cycle unit. The worker should preserve the existing asset APIs when they already
match the task contract, add focused tests or evidence where the proof is weak,
and avoid broad redesign of unrelated `TASK-AR-588..590` surfaces.

## Action Board

| Item | Action |
| --- | --- |
| `TASK-AR-587` | Claim the avatar identity task and audit `patternAgentAvatar` against the acceptance criteria |
| Unit 1 | Prove deterministic self-hosted SVG generation, pinned DiceBear style/version, and no runtime API dependency |
| Unit 2 | Prove role accent token mapping, WCAG contrast, and desktop+mobile console evidence |
| Governance | Re-run design-system, taskset, task identity, browser, and independent verification closeout |

## Next

Re-record anchors:

- `reviews/REVIEW-2026-06-20-taskset-ar-visual-asset-adoption-registration.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`
