---
title: TASK-AR-648 Template Mirror and Pilot Isolation T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-012
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 99
priority: P0
status: approved
tags: [task-ar-648, t3-replan, template-parity, pilot-isolation, repeated-failure]
---

# TASK-AR-648 Template Mirror and Pilot Isolation T3 Replan

## Bottom Line

Proceed only with UNIT-012. Attempt 4 and UNIT-011 are terminal failure
evidence, not repair worktrees. All consumer and release work remains stopped.

## Revalidated Evidence

- Rejected product:
  `dd279cd5613578c87ed6c4c24b37325084449d82`
- Rejected product tree:
  `ea843b6ca5661f04179376df92a11f4416217ab1`
- Rejected template tree:
  `fb7a9ad3dca93b9734467e2e9b5201ba2c1527a9`
- Attempt-4 W4b: `BLOCK`, P0 0 / P1 2 / P2 5
- Packaged taskset SHA:
  `fe840225c2fe9e6a11769d370f3f9920f532bd95fcc20a59a75449ff226652e6`
- Root taskset behavior already passes the same frozen completion state.
- Common-script audit: 84 eligible, 76 identical, 8 divergent.
- Bean attempt 4 remains frozen at
  `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`.
- Allimbot remains untouched and blocked behind a successful future Bean
  replay.

## Dispatch Decision

Re-anchor the taskset to this record, UNIT-012, attempt-4 W4a/W4b/pilot
evidence, the Compound record, all eight divergent paths, Owner-chain parity,
taskset tests, template smoke, and the registration/dispatch scripts. Then
require:

1. plan assumptions pass without bypass;
2. UNIT-012 readiness passes with zero findings;
3. the taskset plan selects UNIT-012 and no blocked historical unit;
4. default claim persistence leaves Runtime HEAD unchanged;
5. RED tests precede product implementation;
6. no consumer checkout is targeted during repair.

## Product Decision

The mirror gate is source-only because an installed host has no canonical
source tree to compare. That omission must be explicit in the template Owner
gate and enforced by chain-parity tests. All five portable fixes themselves
remain installed-host assets.

The pilot-isolation gate is an evaluation control. It distinguishes checkout
roles and requires observed write roots; it does not infer pilot causation from
an unrelated live checkout's before/after mismatch.

## Stop Boundary

Stop on assumption drift, a selector other than UNIT-012, claim SCM mutation,
unbounded exceptions, erased consumer variants, portable feature loss,
isolation fail-open, any Bean/Allimbot/Autofolio write, or any release/external
action.

## Next

Record T3, verify readiness and selection, claim UNIT-012, then add the
fail-before mirror, packaged-time, installed-work, and isolation regressions.
