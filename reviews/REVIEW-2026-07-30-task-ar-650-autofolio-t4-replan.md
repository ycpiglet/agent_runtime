---
title: TASK-AR-650 Autofolio Migration T4 Replan
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: approved
signal: pass
score: 98
priority: P0
tags: [autofolio, t4-replan, migration, direct-claim, scribe, isolation]
---

# TASK-AR-650 Autofolio Migration T4 Replan

## Decision

Proceed to attempt 3 only after committing the direct-claim repair as a new
Runtime candidate. Preserve attempts 1 and 2 as immutable RED products and do
not reuse either partially exercised Autofolio target.

Attempt 2 established that `c110e6df355b960a3c32bd8187eb792b26c8f18f`
repairs the Owner, continuity, taskset, wave, and orchestration paths, but its
direct `task_claim_dispatcher.py create` path still allowed mutation before the
canonical T0 and readiness contract. That is a Runtime P1, not a host-owned
exception.

## Exact Revalidated Inputs

- Runtime attempt-1 RED product/tree:
  `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` /
  `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Runtime attempt-2 RED product/tree:
  `c110e6df355b960a3c32bd8187eb792b26c8f18f` /
  `5ff7e622a0a0220aff9f5dfc0b6810f8032e9c5e`
- Attempt-2 template/scripts trees:
  `e76904546d3f3a215071e3c2cf8878b3cfa62aae` /
  `392d704fe64b5e0a90073d832cf1384dc4180681`
- Autofolio commit/tree:
  `ca88433cf155fd03d616584fda7ed4aa3d33fd71` /
  `c51490efb2249f532c78b03025a3d0c78cca68e7`
- Attempt-2 staging:
  `59 safe_updates`, `0 conflicts`, `170 preserved`, `22 excluded`
- Attempt-2 protected manifest:
  `1804` files /
  `bd97835ce0931b02154a05b538be7543022e070c2ba0f4ef4c76af1f0f49907d`
- Autofolio direct-claim candidate result: `5 passed, 20 failed`.
- Repaired Runtime exact direct-claim host contract: `25 passed`.
- Repaired Runtime authoritative suite:
  `2958 passed, 3 skipped, 4 warnings`.

## Repair Contract

The new candidate must:

1. derive the canonical taskset binding before claim persistence;
2. require a well-formed T0 snapshot when a host has a canonical taskset or a
   complete unit record;
3. reject missing or malformed T0 state even when `--skip-plan-check` is
   supplied;
4. allow that escape only for recorded-anchor drift;
5. apply task, taskset, unit, and unit/taskset-binding readiness before claim,
   handoff, log, instance, pane-event, Git, or worktree mutation;
6. preserve the bounded legacy identity-only claim path; and
7. keep direct, taskset, and wave entry points behaviorally aligned.

The exact Autofolio direct-claim test is a Runtime host contract, and the root
and packaged-template dispatcher files must remain byte-identical.

## Scribe Finding

The pre-commit Scribe check is technically available but operationally stale:
its only conventional source is `STATUS.md`, it selected 10 old entries from
`769` hot records, and the state-sync gate reported that `STATUS.md` does not
contain active `TASK-AR-650`. Writing `SCRIBE-PROJECTION.json` can therefore
produce a projection marked fresh while current task-linked state is absent.

This does not authorize manual status fabrication. Attempt 3 must capture this
as a harness backlog item and distinguish:

- projection freshness;
- source freshness;
- active task/claim coverage; and
- actual compaction or archival work.

The current migration may proceed because Scribe reports
`closure_blocking=false`, but next-version readiness must not call this
accumulation problem solved.

## Attempt-3 Isolation

Create a new detached Runtime product from the post-repair commit and entirely
new Autofolio target/control worktrees at `ca88433c`. Before any target write:

1. capture product, target, control, and primary provenance;
2. create a v2 sorted path/per-file-SHA protected manifest;
3. record primary status, staged, and unstaged observation digests;
4. prove the control and Runtime product are clean; and
5. bind all evidence to attempt 3.

The live primary remains observation-only. Do not copy its uncommitted work.

## Migration And Acceptance

Start from the exact 20 v0.6 unmanaged paths. Reclaim only contracts proven by
the Autofolio host tests. Keep real product context as `host_owned`, preserve
bootstrap state as `seed_once`, and permit no unclassified or silent
overwrite path.

Attempt 3 is green only if:

- direct claim, Owner, continuity, taskset, wave, work schema, and status alias
  host contracts pass;
- the final reconcile has zero conflicts and a second plan/apply is
  idempotent;
- every protected path and frozen-control byte is unchanged;
- exact migration, isolation, and acceptance evidence passes;
- all install, credential, broker, order, provider, network, notification,
  database migration, deploy, commit, push, tag, version, release, package, and
  publication counters are integer zero; and
- no Runtime P0/P1 remains.

W4b must be honestly labeled. If an independent reviewer cannot be invoked
under the active execution policy, do not substitute a same-worker review or
claim the release gate passed.

## Stop Boundary

Stop on plan drift, wrong task selection, primary/control/product write,
unclassified seam, silent overwrite, conflict, protected product mutation,
consumer commit, install, credential read/change, broker/order call, database
migration, network/provider call, notification, deploy, release, version, tag,
package, push, publication, or false independent-review attribution.
