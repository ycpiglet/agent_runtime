---
title: TASK-AR-648 Bean Wiki Attempt-2 Registration
date: 2026-07-29
status: active
signal: pass
score: 98
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-006
tags: [planning-record, bean-wiki, adoption, green-replay, evidence-truth]
---

# TASK-AR-648 Bean Wiki Attempt-2 Registration

## Bottom Line

Register a separately claimed Bean Wiki replay only after UNIT-005's exact
product SHA passed independent W4b. Start from the original Bean baseline,
not the preserved failed attempt.

## Fixed Inputs

| Boundary | Fixed value |
| --- | --- |
| Agent Runtime product | `6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39` |
| Runtime W4b | `APPROVE`, 97/100, no P0/P1 |
| Bean baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean primary | read-only; dirty pre-existing state |
| Frozen attempt 1 | `c93d12baa0020c30e71b50211ecd0c760a65e5e2`; never reuse |
| New path | `.pilot-worktrees/bean-wiki-task-ar-648-green-2` |
| New branch | `codex/task-ar-648-agent-runtime-green-pilot-2` |
| Profile | `core+web-content` |
| Consumer SCM | default `working_tree`; host commits must remain zero |

## Task Routing

| Pilot task | Requested tier | Execution |
| --- | --- | --- |
| adoption and preservation | `worker_low` | deterministic local commands |
| article review | `worker_standard` | one selective editorial specialist |
| restart and Scribe | `worker_low` | deterministic distinct local processes |

Configured provider tiers are not observations. Model, tokens, cost, and
savings remain unavailable unless a provider-sourced record proves them.

## Evidence Rules

- Capture before/after digests for all 16 host assets, `BACKLOG.md`, and the
  complete `src/content/**` manifest.
- Record exact template root, product ref/tree, and projection digest in every
  reconcile stage.
- Map every post-bootstrap Bean diff to one local task/claim.
- Regenerate classifier and other projections only after the final serial
  lifecycle write.
- Keep original red and attempt-1 reports and fixture immutable.
- Create `evidence-green.json` only from observed passing state, then pin its
  complete semantic digest in the validator.

## Stop Boundary

Any P0/P1, primary/frozen-worktree mutation, host/content mutation, consumer
commit, nonzero external effect, false routing/cost observation, or
independent rejection stops Bean and keeps Allimbot and release work blocked.
