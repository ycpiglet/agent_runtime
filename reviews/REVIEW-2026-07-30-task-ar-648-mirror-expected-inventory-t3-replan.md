---
title: TASK-AR-648 Expected Common Mirror Inventory T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-013
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 99
priority: P0
status: approved
tags: [task-ar-648, t3-replan, template-parity, expected-inventory, repeated-failure]
---

# TASK-AR-648 Expected Common Mirror Inventory T3 Replan

## Bottom Line

Proceed only with UNIT-013. Exact product
`f49ff61bb7dcac7466ae76b6cfc775864d1a83ab` and its UNIT-012 reviews are
terminal evidence, not a product to replay in Bean.

## Revalidated Evidence

- Rejected product:
  `f49ff61bb7dcac7466ae76b6cfc775864d1a83ab`
- Rejected product tree:
  `ee1ad9221b6cd79e9ac83b75249bf4948361a4f2`
- Rejected packaged project tree:
  `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f`
- Rejected packaged scripts tree:
  `62311b7847f66206a2a33e4bd497750bf074384f`
- UNIT-012 W4b: `BLOCK`, P0 0 / P1 1 / P2 1
- Current census: 84 common, 81 identical, 3 intentional
- Missing-side fixture: exit 0, zero findings
- Bean attempt 4 remains frozen; attempt 5 does not exist.
- Allimbot and Autofolio remain untouched by this repair.

## Dispatch Decision

Re-anchor the taskset to this record, UNIT-013, UNIT-012 W4a/W4b, the mirror
gate/contract/tests, and registration/dispatch scripts. Then require:

1. plan assumptions pass without bypass;
2. UNIT-013 readiness passes with zero findings;
3. canonical selection resolves UNIT-013 and no blocked historical unit;
4. default claim persistence leaves Runtime HEAD unchanged;
5. missing-side RED tests precede product implementation;
6. no consumer checkout is targeted during repair.

## Product Decision

The contract, not the current tree intersection, owns expected portable path
identity. It pins the exact 84 paths and rejects missing expected sides plus
unexpected common additions. Known one-sided populations remain outside that
contract, while intentional divergences remain digest-pinned members of it.

## Stop Boundary

Stop on assumption drift, a selector other than UNIT-013, claim SCM mutation,
a count-only or dynamically derived baseline, wildcard exceptions, blocked
legitimate one-sided assets, weakened digest pins, any consumer mutation, or
any release/external action.

## Next

Record T3, verify readiness and selection, claim UNIT-013, create Compound
evidence, then add fail-before regressions.
