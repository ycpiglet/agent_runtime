---
title: TASK-AR-648 Template Mirror and Pilot Isolation Repair Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-012
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, template-parity, pilot-isolation, bean-wiki, release-blocker]
---

# TASK-AR-648 Template Mirror and Pilot Isolation Repair Registration

## Bottom Line

Register one Runtime-only unit for the two P1s independently confirmed by Bean
attempt 4. No consumer replay is authorized until the repaired Runtime product
passes canonical W4a and a fresh independent W4b.

## Reproduced Mirror Census

| Class | Count | Decision |
| --- | ---: | --- |
| Common Python/CMD script assets | 84 | Govern the complete intersection |
| Byte-identical | 76 | Require continued identity |
| Divergent | 8 | Classify and repair or pin explicitly |
| Unsynchronized portable fixes | 5 | Copy canonical root behavior into package |
| Intentional source/consumer variants | 3 | Preserve with reason and both digests |

The five product defects are packaged copies of
`collaboration_concurrency_gate.py`, `collaboration_governance_gate.py`,
`footprint_conflict_gate.py`, `now.py`, and `taskset_work_gate.py`.

The three intentional variants are:

| Path | Reason |
| --- | --- |
| `compound_record.py` | Root is a thin package entrypoint; installed hosts need a standalone implementation. |
| `owner_governance_gate.py` | Source runs repository-only checks; installed hosts use explicit substrate-aware skips and omissions. |
| `stop_hook_owner_governance.py` | Installed hosts intentionally pass the empty-owner-doc compatibility flag; source emits its own governance summary. |

An exception is not a wildcard. It must pin the current SHA-256 of both sides,
and becomes invalid when either implementation changes or the files become
identical.

## Isolation Decision

Snapshot inequality is evidence of change, not evidence of causation.

| Checkout role | Allowed outcome |
| --- | --- |
| Disposable target | Changes allowed only inside its declared root and write surface |
| Frozen control/evidence | Any HEAD, status, or tracked-diff change blocks |
| Live observation | Unattributed drift is recorded as a watch; observed targeting or writes block |

Canonical roots must be disjoint. The authorized write roots are exactly the
disposable targets. This keeps prior attempts and product evidence immutable
without pretending that an independently edited live primary is controlled by
the pilot.

## Verification Boundary

The unit must prove packaged taskset ISO-second freshness, installed
`work.py now`, portable collaboration/footprint parity, source Owner-chain
enforcement, consumer-chain omission documentation, and the isolation decision
matrix. It then runs the complete Runtime suite and independent review on one
exact product.

## Exclusions

- No Bean, Allimbot, Autofolio, or frozen-pilot mutation
- No attempt-5 worktree
- No release, version, tag, package, push, publish, or deploy
- No provider-live execution, dependency installation, credential access, or
  network delivery

## Next

Record the T3 assumption snapshot, prove UNIT-012 readiness and canonical
selection, create a default working-tree Runtime claim, then write RED tests.
