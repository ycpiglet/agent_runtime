---
title: TASK-AR-648 Pilot Evidence Contract T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-015
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 99
priority: P0
status: approved
tags: [task-ar-648, t3-replan, pilot-contract, sanitized-projection, exact-evidence]
---

# TASK-AR-648 Pilot Evidence Contract T3 Replan

## Bottom Line

Proceed only with UNIT-015. UNIT-014 is immutable blocked evidence; the Bean
consumer is not a repair surface. The next product must close both evidence
P1s before any new consumer replay.

## Revalidated Evidence

- UNIT-014 W4a and fresh independent W4b both return
  `BLOCK`, Runtime P0 0 / P1 2 / P2 2.
- The green fixture is internally consistent and path-sanitized but is refused
  by twelve values from the sole embedded red contract.
- The raw isolation fixture passes with zero blocks/watches but the public
  sanitizer reports one local-path finding.
- Existing focused isolation/acceptance tests pass 21/21, proving the defects
  are missing contracts rather than unrelated regression noise.
- Bean attempt 5, control 5, primary, and Allimbot are outside the UNIT-015
  write set.

## Technical Decision

Use strict JSON contract records discovered from one repository-owned
directory and indexed by exact `(host, pilot_id)`. Validate the registry before
selecting a record. Contract data may refine exact run expectations but may
not disable generic executable rules.

Support two isolation evidence modes:

1. v1 raw evidence validates real absolute roots, disjointness, and write
   containment;
2. v2 sanitized projection validates public identity/snapshot/attribution
   semantics and an exact raw-evidence digest plus raw-gate decision.

Projection generation must first run v1 validation and refuse any raw blocker.
The persisted v2 fixture must contain no absolute local path.

## Dispatch Decision

Require the normal T3 assumption gate, UNIT-015 readiness, and canonical
selection. Use a default working-tree claim and prove Runtime HEAD is unchanged
by claim creation. Planner escalation is appropriate because the repair is
cross-cutting, data-integrity-sensitive, and follows repeated pilot failure;
provider/model execution remains unobserved.

## Pre-claim Proof

- Plan assumptions: pass, zero findings
- UNIT-015 readiness: pass, zero findings
- Canonical selection: `TASK-AR-648` / `UNIT-TASK-AR-648-015`
- Requested worker tier: `worker_standard`
- Policy-selected orchestration tier: `planner_high`
- Escalation signals: `cross_cutting`, `data_integrity`, `repeated_failure`
- Default claim:
  `CLAIM-20260730-054522-task-ar-648-ar648015`
- Runtime HEAD before/after claim:
  `598c960bb4431209013e71fea1fa2d0fd0d0bf56`
- Consumer worktree creation or write: zero
- Provider/model execution observation: unavailable

## Exit Decision

No new Bean replay follows merely because focused tests pass. UNIT-015 needs
canonical W4a, fresh independent W4b, full sanitizer/governance, and the full
test suite on one exact product. Any P0/P1 creates a separate repair unit.
