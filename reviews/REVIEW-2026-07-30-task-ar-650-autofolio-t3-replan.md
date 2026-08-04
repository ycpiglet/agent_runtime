---
title: TASK-AR-650 Autofolio Migration T3 Replan
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: approved
signal: pass
score: 98
priority: P0
tags: [autofolio, t3-replan, migration, ownership, isolation, taskset-order]
---

# TASK-AR-650 Autofolio Migration T3 Replan

## Bottom Line

Proceed only from exact Runtime product
`4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` and clean Autofolio commit
`ca88433cf155fd03d616584fda7ed4aa3d33fd71`. Bean Wiki and Allimbot are
independently green. The live Autofolio primary contains concurrent Owner work
and is a read-only observation, never the migration target.

The registration context said 21 unmanaged paths. The pinned v0.6
`agent_runtime.yml` contains exactly 20. The migration must classify those 20
paths individually and must not preserve the stale count as an acceptance
claim.

## Revalidated Evidence

- Runtime lifecycle baseline: `dd741b23`
- Runtime product/tree:
  `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` /
  `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Runtime template/scripts trees:
  `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f` /
  `62311b7847f66206a2a33e4bd497750bf074384f`
- Autofolio commit/tree:
  `ca88433cf155fd03d616584fda7ed4aa3d33fd71` /
  `c51490efb2249f532c78b03025a3d0c78cca68e7`
- Autofolio v0.6 lock: `agent-runtime-lock/v1`, package `0.6.0`,
  256 template files.
- Live-primary W0 status, unstaged-diff, and staged-diff digests:
  `b4409298f3af07c0924dbd0da148a53f0fd0d35e1f64bdb1480507c15efbda2a`,
  `beb38c6dae562f72bc076b649ddef6533815b8b22df717f1070c63a54508c9c0`,
  and
  `30a0fa4d42e8b087cba249a1c0a58af19eb951e5a145ac957ea133e227c89bcd`.
  These are observation anchors, not content to copy.
- Bean attempt 6 and Allimbot attempt 1: exact acceptance and independent
  W4b pass with no Runtime P0/P1.

## Dispatch Defect And Preflight Hardening

At W0, `taskset_dispatcher.py plan` selected `TASK-AR-651` before open
`TASK-AR-650`, even though the registered plan and live pointer require the
migration before RC assembly. `work.py new` retained taskset identity in
`TASKSET-DEFINITIONS.json` but discarded the registration input's ordered task
membership. Score fallback therefore reordered two P0 tasks.

This is the same defect class observed during the Allimbot consumer replay.
Before relying on taskset dispatch for RC work:

1. preserve the ordered task IDs in the work-generated taskset registry;
2. consume that list as strict canonical membership;
3. remain backward compatible with registry rows that predate the list;
4. fail closed on duplicate, unknown, omitted, or wrong-taskset members; and
5. prove the current taskset selects `TASK-AR-650`, then `TASK-AR-651`.

Direct canonical claim creation for `TASK-AR-650` remains allowed after T3
re-anchoring and readiness pass. It must not use `--skip-plan-check`.

## Migration Shape

Use v2 `full-runtime` to retain Autofolio's existing capability envelope. Add
the canonical `agents/host/HOST-CONTEXT.yml`, point Scribe at the host-owned
`agents/lead_engineer/STATUS.md`, declare the generated projection, and record
trading, broker, risk, credential, migration, workflow, and order surfaces as
read-only risk paths.

Every old v1 unmanaged entry receives exactly one disposition:

- `managed`: an upstream Runtime implementation now supersedes a temporary
  downstream repair and passes host verification;
- `seed_once`: an existing host-customized bootstrap/state file is preserved;
- `host_owned`: product context, operating data, or a still-required host
  compatibility seam remains explicitly owned by Autofolio;
- `temporary_conflict`: only if evidence proves neither safe adoption nor
  explicit ownership is currently sound.

The expected migration starts from 20 untyped unmanaged entries, ends with
zero `sync.unmanaged` entries, zero unclassified paths, and zero conflicts.
The report must quantify how many paths become managed, seed-once, or
host-owned; it must not call an ownership rename a seam reduction unless a
temporary fork actually returns to managed Runtime.

## Isolation And Product Boundary

Create one disposable target and one same-commit frozen control only after the
Runtime claim exists. Capture primary, target, control, Runtime lifecycle, and
exact product baselines before the first target write.

Runtime projection changes are allowed only in the disposable target.
Protected Autofolio product surfaces include `app/**`, `web/**`,
`supabase/**`, databases, dependency manifests and locks, trading scripts,
credentials, environment files, and deployment configuration. Their
before/after inventory and content digests must match. No live/paper broker
call, order, token request, database migration, notification, provider call,
credential read, install, commit, push, deploy, or release action is allowed.

## Acceptance Decision

Autofolio is migration-green only if:

1. ordered taskset membership is durable and selects 650 before 651;
2. v0.6-to-v0.8 config, ownership, and lock migration is deterministic;
3. all 20 old unmanaged paths are dispositioned with zero conflicts and at
   least one evidenced temporary fork returns to managed Runtime;
4. a second reconcile/apply is idempotent;
5. protected product and frozen-control bytes do not change;
6. no-install host verification, Compound/Scribe, continuity, taskset, Owner,
   and exact isolation/acceptance gates pass;
7. every external-effect counter is integer zero; and
8. W4a and fresh independent W4b contain no Runtime P0/P1.

## Stop Boundary

Stop on plan drift, wrong task selection, primary/control/product write,
unclassified legacy seam, silent overwrite, conflict, protected product
mutation, consumer commit, package install, credential access, KIS/broker/order
call, database migration, network/provider call, notification, deploy, release,
version, tag, package, push, or publication action.
