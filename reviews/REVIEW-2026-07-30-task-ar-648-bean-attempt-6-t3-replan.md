---
title: TASK-AR-648 Bean Wiki Attempt 6 T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-016
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 99
priority: P0
status: approved
tags: [task-ar-648, t3-replan, bean-wiki, exact-contract, sanitized-isolation]
---

# TASK-AR-648 Bean Wiki Attempt 6 T3 Replan

## Bottom Line

Proceed only with UNIT-016 against Runtime product
`4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`. UNIT-014 is immutable blocked
evidence; UNIT-015 is completed Runtime repair evidence. No Runtime product
modification belongs in this replay.

## Revalidated Evidence

- Product: `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`
- Product tree: `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Packaged template tree: `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f`
- Packaged scripts tree: `62311b7847f66206a2a33e4bd497750bf074384f`
- Product mirror census: 84 expected, 84 current, 81 identical, 3 intentional
- Product verification: `2739 passed, 3 skipped`
- UNIT-015 W4a/W4b: APPROVE, P0 0 / P1 0 / P2 1
- Bean baseline: `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Attempt 6 and control 6 do not yet exist.
- Historical red and attempt-5 fixtures pass their exact contracts.
- Attempt-5 public isolation evidence is path-free and raw-digest-bound.
- Allimbot remains untouched and blocked.

## Dispatch Decision

Re-anchor the taskset to this record, UNIT-016, UNIT-015 reviews, acceptance
and isolation contracts, validators, and claim/work dispatchers. Then require:

1. plan assumptions pass without bypass;
2. UNIT-016 readiness passes with zero findings;
3. canonical selection resolves UNIT-016, not a historical blocked unit;
4. the default Runtime claim leaves Runtime HEAD unchanged;
5. exact product and both fresh Bean worktrees exist before snapshot capture;
6. no consumer write begins until control and live-observation baselines are
   recorded.

## Execution Decision

Run exactly three Bean traces. Deterministic adoption and restart/Scribe stay
on `worker_low`; one editorial review alone selects `worker_standard`.
Preserve all host/content bytes, keep claims in working-tree mode, and report
provider observations as unavailable unless actually observed.

## Pre-claim Proof Required

- UNIT-016 readiness: pass, zero findings
- Canonical taskset selection: `TASK-AR-648` /
  `UNIT-TASK-AR-648-016`
- Requested Runtime tier: `worker_standard`
- Policy-selected orchestration tier: `planner_high` only for declared
  `cross_cutting`, `data_integrity`, and `repeated_failure` signals
- Provider/model execution: not observed
- Consumer worktrees created before claim: zero

## Stop Boundary

Stop on assumption drift, wrong selection, Runtime product drift,
frozen-control change, observed write outside attempt 6, unsupported
causality, consumer commit, content mutation, raw/projection binding loss,
contract ambiguity, external effect, Allimbot action, or any release surface.
