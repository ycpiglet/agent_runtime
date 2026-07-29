---
title: TASK-AR-648 Expected Common Mirror Inventory Repair Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-013
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, template-parity, expected-inventory, fail-closed, release-blocker]
---

# TASK-AR-648 Expected Common Mirror Inventory Repair Registration

## Bottom Line

Register one narrow Runtime-only unit for the P1 independently confirmed in
UNIT-012. No Bean attempt 5, Allimbot pilot, or release action is authorized
until the repaired exact product passes W4a and fresh independent W4b.

## Registration Path

`work.py new` creates a complete new initiative/taskset/task graph and rejects
a mix of already-existing parent records plus a newly appended unit as partial
existing state. TASK-AR-648 is already canonical, so this follow-up uses the
repository's established existing-task path: add one canonical unit spec,
refresh generated views, and explicitly record the T0/T3 assumption snapshot
with `plan_assumption_gate.py record`. This limitation is visible rather than
bypassed with `--no-plan-snapshot` or `--skip-plan-check`.

## Reproduced Defect

The rejected gate compares:

```text
current source paths ∩ current template paths
```

Deleting one side removes that path from the intersection. A minimal fixture
with `source_only.py`, an empty template directory, and a valid empty
divergence map exits zero with no finding. The same is true in the opposite
direction. Today's `84 common / 81 identical / 3 intentional` census therefore
describes state but does not pin the future portable surface.

## Contract Decision

The mirror contract will carry the exact sorted list of all 84 expected common
Python/CMD paths.

| Actual state | Decision |
| --- | --- |
| Expected and present on both sides | Compare bytes or validate pinned divergence |
| Expected but source missing | Block |
| Expected but template missing | Block |
| Common on both sides but not expected | Block pending reviewed inventory update |
| Root-only and not expected | Allow |
| Template-only and not expected | Allow |

Inventory entries must be unique, safe, normalized relative paths with eligible
suffixes. The three intentional divergence records must be a subset of this
inventory and keep both exact digests.

## Model-Economy Decision

The implementation surface is three product/test files and has executable
acceptance criteria, so its baseline tier remains `worker_standard`. Dispatch
may escalate this single claim because the defect is cross-cutting,
data-integrity-sensitive, and repeated. That escalation is scoped to the
repair and independent review; it does not change the repository's default
worker tier or authorize provider-live claims.

## Exclusions

- No change to pilot isolation or portable script bodies
- No Bean Wiki, Allimbot, Autofolio, or frozen-pilot mutation
- No release, version, tag, package, push, publish, or deploy
- No dependency installation, credential access, or network delivery

## Next

Record T3 assumptions, prove readiness and selection, create a default
working-tree claim, then commit the missing-side RED suite before product
implementation.
