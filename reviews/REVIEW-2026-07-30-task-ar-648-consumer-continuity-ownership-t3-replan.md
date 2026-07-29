---
title: TASK-AR-648 Consumer Continuity Ownership T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-010
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 98
priority: P1
status: approved
tags: [task-ar-648, t3-replan, continuity, ownership, fail-closed]
---

# Consumer Continuity Ownership T3 Replan

## Bottom Line

Proceed only with UNIT-010. The prior snapshot drift is fully explained by the
blocked UNIT-009 lifecycle, Bean attempt-3 evidence, classifier/board
regeneration, and independent W4b. No previous blocked unit may become a
dispatch fallback.

## T2 Drift Disposition

The old snapshot reports changes in TASK-AR-648 and UNIT-009. Those are the
expected results of registering, claiming, blocking, independently reviewing,
and releasing the attempt-3 replay. Product code still has zero delta from
`b82042eba58f1e06e1e73130a189cb72245462a0`.

## Repair Contract

1. Source mode remains strict and continues reading the Runtime repository
   README/protocol templates.
2. Consumer mode requires a valid v2 config and v2 lock whose project and
   ownership facts agree.
3. Runtime wording moves to or is validated from a managed Runtime contract
   surface; host-owned docs are not rewritten.
4. Pointer required fields and schema are always checked.
5. Missing/malformed config, lock, managed contract, or pointer blocks.
6. A clean installed-host Owner-governance journey is mandatory before W4b.

## Dispatch Decision

Re-record assumptions on the finding evidence, root and packaged gate,
configuration parser, managed Runtime document, focused tests, TASK-AR-648,
UNIT-010, and selector/claim dispatchers. Then require:

- plan assumptions pass without bypass;
- UNIT-010 readiness passes;
- the taskset selector chooses only UNIT-010;
- the default Runtime claim leaves HEAD unchanged;
- no Bean or Allimbot path is modified.

## Stop Boundary

Stop on any blanket consumer skip, source-mode weakening, pointer fail-open,
unproven ownership exemption, consumer workaround, P0/P1 regression, release
action, or external effect.
