---
title: Autofolio v0.8 Migration Pilot - Green Attempt 3
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
pilot_id: autofolio-v080-green-attempt-3
status: passed
signal: pass
runtime_verdict: TECHNICAL_PASS
release_verdict: BLOCKED
finding_counts: {P0: 0, P1: 2, P2: 1}
runtime_product: db025d783168b4934ef1260bab0b0b635c9b8f39
host_commit: ca88433cf155fd03d616584fda7ed4aa3d33fd71
tags: [autofolio, migration, exact-product, attempt-3, green, release-blocked]
---

# Autofolio v0.8 Migration Pilot - Green Attempt 3

## Bottom line

Autofolio migration attempt 3 is a technical pass. Exact Runtime product
`db025d783168b4934ef1260bab0b0b635c9b8f39` migrated a fresh disposable
Autofolio checkout from its v0.6 ownership configuration to the v0.8
full-runtime profile, classified all 20 legacy seams, reclaimed eight real
Runtime forks, preserved all 1,804 protected product files byte-for-byte, and
converged to a conflict-free idempotent result.

The migration did not execute a product task or fabricate task, claim, restart,
model-use, or savings evidence. The frozen control, detached Runtime product,
and live Autofolio primary were observation-only and remained unchanged.

This pass does **not** make the Runtime release-ready. Actual model/cost
observation and Scribe source-debt handling remain P1, legacy hook duplication
remains P2, and the exact candidate still requires W4a plus a genuinely
independent W4b. Version, tag, push, package, publish, deploy, and release were
not performed.

## Exact boundary

| Surface | Exact identity | Result |
| --- | --- | --- |
| Runtime product | `db025d783168b4934ef1260bab0b0b635c9b8f39` | detached checkout clean |
| Runtime tree | `bb1e2c9c79dde8de3775a4740e1cefa5022d92b7` | pinned |
| Runtime template tree | `52dbe6e673bf7c18314591d56c78de36bf88625a` | pinned |
| Runtime template scripts tree | `bbd6035c01cf80bd9125bc2a540f4b23988937d9` | pinned |
| Autofolio target/control | `ca88433cf155fd03d616584fda7ed4aa3d33fd71` | target-only Runtime projection; control clean |
| Autofolio live primary | same HEAD with pre-existing owner work | observation-only and unchanged |
| Consumer commits/pushes | not authorized | `0 / 0` |

The target and control were newly created for attempt 3. Neither red attempt's
partially synchronized target was reused. The live primary's before/after
porcelain and tracked-diff digests remained respectively
`b4409298f3af07c0924dbd0da148a53f0fd0d35e1f64bdb1480507c15efbda2a`
and
`beb38c6dae562f72bc076b649ddef6533815b8b22df717f1070c63a54508c9c0`.

## Migration and seam result

The source v0.6 configuration contained exactly 20 unmanaged paths. The
portable seam ledger independently recounts:

| Disposition | Count | Meaning |
| --- | ---: | --- |
| managed | 6 | downstream Runtime behavior returned to the canonical core |
| seed_once | 5 | bootstrap/live state preserved after initial projection |
| host_owned | 9 | Autofolio policy, product schema, or accumulated operating data |
| generated | 0 | none among the 20 source seams |
| unclassified | 0 | no unexplained seam |
| temporary conflict | 0 | no remaining temporary fork |

Seven of the 20 source paths changed during the bounded migration. In addition,
`scripts/status_alias.py` and `scripts/task_claim_dispatcher.py` were reclaimed
as managed Runtime assets. This is a real reduction in temporary downstream
repairs, not merely a rename from unmanaged to host-owned.

The v2 target selected `core`, `web-content`, and `security-service` with 251
template files. Initial reconcile reported 59 safe updates, 170 preserved, 22
excluded, and zero conflicts. Final reconcile reported zero safe updates, 237
preserved, 14 excluded, and zero conflicts. Effective ownership converged to
229 managed, 8 seed-once, and 14 host-owned files.

The lock is `agent-runtime-lock/v2`, points to the exact Runtime commit, carries
template digest
`sha256:d8a663bc65fac51f05d68e3db203311a79aeff8408a1dffb812e3ffaabaaf992`,
and has zero findings. The package field remains `0.7.0`; this pilot did not
authorize a version change.

## Idempotence and product preservation

The second plan/apply cycle left every bounded state digest identical:
porcelain status, tracked diff, untracked paths and content, config, lock,
hooks, and Scribe projection.

The protected inventory contains 1,804 app, web, Supabase, database,
dependency, trading, credential, workflow, and deployment files. Its sorted
path digest is
`f095e32b66baba5bcbaa1e0ec13b2810c1e8705d72581096175798c196eeefb9`;
the before and after byte-manifest digest is identically
`bd97835ce0931b02154a05b538be7543022e070c2ba0f4ef4c76af1f0f49907d`.
Protected changes: `0`.

Rollback is to discard the disposable target. No primary, control, or Runtime
product restoration is required.

## Host contract and lifecycle evidence

All 210 exact Autofolio host-contract tests passed:

| Contract | Passed |
| --- | ---: |
| Owner governance | 13 |
| parallel worktree continuity | 9 |
| direct task claim | 25 |
| taskset dispatch | 85 |
| wave dispatch | 59 |
| lifecycle hooks | 19 |

The attempt recorded and retrieved canonical Compound record
`COMPOUND-20260730-104500-keep-claim-readiness-identical-across-entry-poin-d3f21753dc80`
for defect signature
`defect:direct-claim-bypassed-taskset-readiness-prefligh:d7bbee801435e1f4`.
Search moved from zero to one match and the Compound check passed. The legacy
Compound source remained byte-identical.

Scribe refreshed only its generated projection. The source status stayed
byte-identical, but it still contains 272 hot items and is overdue; only 10
items were selected, active-task coverage is unverified, and no compaction was
performed. This is recorded as a P1 rather than hidden behind the projection's
`fresh/ready` status.

The canonical hook surface contains five events and six Runtime commands, and
the Autofolio Owner-authority command was preserved. Two test-pinned legacy
commands duplicate canonical behavior and remain a P2 migration follow-up.

## Isolation and exact acceptance

Only the disposable Autofolio target was an observed write checkout. Raw
physical-root isolation passed with zero blockers and zero watches. Its
private byte SHA-256 is
`09a4dbc39b62a48e2d299c6d79722cdf5b547776310806ef05e452553d219a27`.

The public path-free isolation projection has semantic SHA-256
`dfc5889c7e51cc318240250199b3d90f50e4ba236654e638ac22608288f51c9a`
and binds the raw proof. The public seam ledger has semantic SHA-256
`76f3928297175567fdb94e62ec7b417a552f306d39b2e4d685805e95ef7d6db0`.

The strict migration contract
`autofolio:autofolio-v080-green-attempt-3` binds evidence semantic SHA-256
`1b3d702f012a2875e44df91b7391db7bce074f2e41e2929ed2bf7dd6193fec6b`,
the exact Runtime and host baselines, both artifact identities, seam recount,
protected-byte proof, idempotence, verification counts, and all required
integer-zero effects. Isolation and acceptance both pass with zero findings.

This is a migration-only contract. `product_work_dispatch_count` and
`product_claim_mutation_count` are both zero; continuity is verified by
contract replay instead of fake product execution.

## External-effect ledger

Publish, deploy, origin push, host commit, credential read/change, network
delivery, provider call, notification, broker call, order, package install,
database migration, content/product mutation, version change, tag, and package
build are all integer zero.

## Findings and release consequence

| Priority | Finding | Required follow-up |
| --- | --- | --- |
| P1 | requested model tiers collapse at execution and no actual model/token/cost receipt exists | TASK-AR-652 |
| P1 | Scribe projection is fresh while source debt is overdue and active-task coverage is unverified | TASK-AR-653 |
| P2 | two legacy hook commands duplicate canonical lifecycle commands | TASK-AR-656 |

Related release-critical work also covers repeated-failure Compound enforcement
(TASK-AR-654), task-claim heartbeat/expiry truth (TASK-AR-655), and consumer
adoption/failure skills (TASK-AR-657). Read-only Runtime health UI is tracked
separately as P2 in TASK-AR-658.

## Decision

Accept attempt 3 as the exact Autofolio migration rehearsal and as evidence
that one shared Runtime plus profile, host overlay, and explicit seams can
replace per-project harness forks.

Keep TASK-AR-650 and the v0.8 RC blocked until the final Runtime candidate
passes W4a and a fresh independent W4b. Keep TASK-AR-651 dependent on
TASK-AR-652 through TASK-AR-657. Do not version, tag, push, build, publish,
deploy, or release without explicit Owner approval.
