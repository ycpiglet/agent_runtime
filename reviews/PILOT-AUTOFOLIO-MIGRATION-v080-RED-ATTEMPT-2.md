---
title: Autofolio v0.8 Migration Pilot - Red Attempt 2
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
status: failed
signal: red
severity: P1
runtime_product: c110e6df355b960a3c32bd8187eb792b26c8f18f
host_commit: ca88433cf155fd03d616584fda7ed4aa3d33fd71
tags: [autofolio, migration, exact-product, direct-claim, red]
---

# Autofolio v0.8 Migration Pilot - Red Attempt 2

## Decision

Do not promote Runtime product
`c110e6df355b960a3c32bd8187eb792b26c8f18f` as the Autofolio migration
candidate. Attempt 2 proved that the Owner, continuity, taskset, and wave
repairs work in the real host, but exposed a second P1 entry-point gap:
`task_claim_dispatcher.py create` did not apply the same T0 and readiness
pre-mutation contract when called directly.

The failing candidate file was restored immediately from the byte-preserved
host backup. The Autofolio primary and frozen control were not modified.
There was no consumer commit, tag, release, provider call, credential access,
broker call, order, deployment, or migration.

## Exact Inputs

- Runtime product / tree:
  `c110e6df355b960a3c32bd8187eb792b26c8f18f` /
  `5ff7e622a0a0220aff9f5dfc0b6810f8032e9c5e`
- Runtime template / scripts trees:
  `e76904546d3f3a215071e3c2cf8878b3cfa62aae` /
  `392d704fe64b5e0a90073d832cf1384dc4180681`
- Autofolio commit / tree:
  `ca88433cf155fd03d616584fda7ed4aa3d33fd71` /
  `c51490efb2249f532c78b03025a3d0c78cca68e7`
- Exact staging reconcile:
  `59 safe_updates`, `0 conflicts`, `170 preserved`, `22 excluded`
- Protected tracked manifest:
  `1804` files /
  `bd97835ce0931b02154a05b538be7543022e070c2ba0f4ef4c76af1f0f49907d`
- Protected manifest format:
  sorted repo-relative path plus per-file SHA-256, followed by SHA-256 of the
  manifest. This supersedes the unreproducible single aggregate recorded by
  attempt 1.

Python module provenance was checked explicitly before each authoritative
Runtime command. The accepted module and template root both resolved inside
the detached `c110e6df` product checkout.

## Causal Results

After `sync --apply-safe`, the preserved Autofolio safety baseline passed:
`210 passed`.

| Candidate seam | Result | Disposition |
|---|---:|---|
| `scripts/agent_orchestrator.py` | syntax, help, dry-run spawn passed | reclaimable |
| `agents/project/WORK-SCHEMA.yml` | `work_schema_gate.py --check` passed | reclaimable |
| `scripts/owner_governance_gate.py` | 13 passed | reclaimable |
| `scripts/parallel_worktree_gate.py` | 9 passed | reclaimable |
| `scripts/status_alias.py` | exact byte match | no real divergence |
| `scripts/taskset_dispatcher.py` | 85 passed | reclaimable |
| `scripts/wave_dispatcher.py` | 59 passed | reclaimable |
| `scripts/task_claim_dispatcher.py` | 5 passed, 20 failed | Runtime repair required |

The direct-claim failures covered missing or malformed T0 state, drifted
anchors, non-ready units, blocked or held task and taskset states, localized
statuses, unit/taskset binding mismatch, and mutation-free refusal. The
candidate created claims in cases where the host contract requires refusal
before claim, handoff, log, instance, pane-event, worktree, or Git mutation.

Private evidence digests:

- Preserved baseline JUnit:
  `24d6be4348bc60f2bf945c78873451d725e2d39e4992881d0db1649e26fb8213`
- Owner candidate JUnit:
  `6a270e52df4a18a779e177328e3b7dee97ad991ac8a04612ceb2666576cebcf6`
- Parallel candidate JUnit:
  `0e98f8c783ed50132920dcd17edfe89e844dce549499a248865c32d326dbf61e`
- Direct-claim candidate JUnit:
  `9cc10c3934ec23a29e7f71e6ed16a813e62a69e21a582c4ee95d94ed45048163`
- Taskset candidate JUnit:
  `2594c856c730842671de8eecf03825114e49c810ccca9c7cd1c2d78c9660af02`
- Wave candidate JUnit:
  `00fdec2aa4b7001f0b9b1bd89d0d25831330d8e04daa7402dc843b49d67d2de4`
- Staging reconcile JSON:
  `2907b6dfedd80f7ea5f3cf4a300c4624de2ab51317fe4dee4554cbdfd53fa008`

## Required Runtime Repair

Before attempt 3:

1. make direct, taskset, and wave claim entry points share T0 and readiness
   refusal before all persistence and external effects;
2. fail closed on missing or malformed T0 for hosts that have adopted a
   canonical taskset or complete unit work graph;
3. retain a clearly bounded migration-compatible path for legacy
   identity-only claims that have not adopted structured work records;
4. promote the exact Autofolio direct-claim contract into Runtime tests; and
5. produce a new exact Runtime commit, clean detached product, and fresh
   Autofolio target/control pair.

Attempt 3 must not reuse the partially synchronized attempt-2 target.
