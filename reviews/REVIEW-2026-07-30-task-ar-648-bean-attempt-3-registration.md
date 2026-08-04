---
title: TASK-AR-648 Bean Wiki Attempt-3 Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-009
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, bean-wiki, adoption, green-replay, portable-continuity, evidence-truth]
---

# TASK-AR-648 Bean Wiki Attempt-3 Registration

## Bottom Line

Register one fresh Bean Wiki replay only after the portable-continuity product
passed canonical W4a, fresh independent W4b, and canonical verification.
Neither failed Bean worktree is a repair target or starting point.

## Signal

Pass for registration of one bounded, reversible attempt. The preceding P0
has exact-product W4a, independent W4b, canonical verification, a released
claim, and a closed Runtime unit.

## Fixed Inputs

| Boundary | Fixed value |
| --- | --- |
| Runtime product | `b82042eba58f1e06e1e73130a189cb72245462a0` |
| Product template tree | `d61713bc4066d4ea549efcc7826da10929e64e94` |
| Runtime lifecycle close | `da15ddf6c9e06c89368b3ccc53c4fca603165b1b` |
| Runtime W4b | `APPROVE`, 99/100, no P0/P1 |
| Runtime canonical verification | focused `294`, routing `49`, full `2678 passed, 3 skipped` |
| Bean baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean primary | read-only; dirty owner state |
| Original red pilot | read-only at `.pilot-worktrees/bean-wiki-task-ar-648` |
| Frozen attempt 1 | read-only at `.pilot-worktrees/bean-wiki-task-ar-648-green` |
| Frozen attempt 2 | read-only at `.pilot-worktrees/bean-wiki-task-ar-648-green-2` |
| New path | `.pilot-worktrees/bean-wiki-task-ar-648-green-3` |
| New branch | `codex/task-ar-648-agent-runtime-green-pilot-3` |
| Profile | `core+web-content` |
| Consumer SCM | default `working_tree`; consumer commits remain zero |

The Runtime lifecycle commits after `b82042eb` change only governance
evidence. Product and pilot-validator surfaces have zero delta from the exact
approved product.

## Routing

| Pilot task | Requested tier | Permitted execution |
| --- | --- | --- |
| adoption and preservation | `worker_low` | deterministic local commands |
| article review | `worker_standard` | one selective read-only editorial specialist |
| restart and Scribe | `worker_low` | deterministic distinct local processes |

The Bean editorial review follows `bean-wiki-editorial-ops`: it reads
`AGENTS.md`, the editorial SSOT, specialist guidance, configured review skill,
personas, and the article, then writes only a bounded review artifact.
Configured tiers are not observed models. Model, usage, token, cost, and
savings observations stay unavailable without provider evidence.

## Evidence Contract

1. Capture exact Runtime ref, tree, template-tree, template-root, and semantic
   digest in every adoption stage.
2. Capture before and after digests for all declared host assets,
   `BACKLOG.md`, `coffee-flavor-wheel.html`, and every `src/content/**` file.
3. Prove the no-STATUS bootstrap uses the canonical standby pointer and that
   the first default claim plus deterministic projection passes pointer,
   claim, handoff, and log agreement.
4. Map every post-bootstrap Bean diff to one local task and claim.
5. Complete exactly three task/unit/claim traces and keep each routing field
   semantically distinct.
6. Run local content/editorial checks without installing dependencies or
   using the network; never edit the generated index by hand.
7. Keep every external-effect counter, including dependency installation and
   content mutation, at integer zero.
8. Create the sanitized green fixture only from observed passing state and
   obtain exact-product W4a plus independent W4b before Allimbot.

## Action

T3-anchor UNIT-009, require readiness and canonical plan selection, create a
default working-tree Runtime claim, and only then create the new Bean
worktree.

## Decision

Use a fresh attempt rather than repairing a failure. Keep the Runtime core
portable and preserve Bean's editorial harness as a host-owned overlay.

## Risk

The main risks are provenance ambiguity, a continuity path that passes on
partial state, accidental content mutation, and configured model tiers being
reported as observations. Each is an explicit fail-closed acceptance check.

## Stop Boundary

Any P0/P1, primary or frozen-worktree mutation, provenance ambiguity,
continuity mismatch, host/content mutation, consumer commit, dependency
installation, false routing or cost observation, nonzero external effect,
Allimbot action, or release action stops the replay and preserves attempt 3 as
failure evidence.

## Next

Record the T3 assumptions and prove the selector chooses only UNIT-009. No
consumer path may be created before the Runtime claim exists.
