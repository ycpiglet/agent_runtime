---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-preverify-transaction-truth
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-preverify-audit
reviewer: codex-task-ar-654-preverify-review-group
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 5, P2: 3}
baseline_commit: d2882e786fea00d79dd7acad6339a9e89ada57e7
baseline_tree: b1dff7f5132c5e6dcb0b965666ebcc586fcc902e
candidate_kind: uncommitted-working-tree
release_authorized: false
created_at: 2026-08-02T18:41:09+09:00
tags: [task-ar-654, preverify, post-commit, snapshot, work-status, strict-json, sync, role-overlay]
---

# TASK-AR-654 preverify transaction-truth audit

## Verdict

`REVISE — P0: 0, P1: 5, P2: 3.`

The dirty candidate passed the focused Runtime suite (`1495 passed, 8
skipped`) and the complete local suite (`4208 passed, 11 skipped`, four known
UI deprecation warnings). Three independent read-only reviews nevertheless
reproduced untested authority seams. A green baseline does not authorize
release while those races and fail-open paths remain outside the regression
matrix.

## P1 findings

1. Dispatcher and role-overlay publication commit a no-clobber artifact and
   then re-open the path to capture rollback ownership. If that fallible
   capture raises, the operation reports failure while the unregistered
   artifact remains and blocks retry.
2. Atomic publication may commit the destination and then propagate an error
   from closing the validated parent directory descriptor. The durable result
   and reported result disagree.
3. Claim-store mutation may complete and then propagate an error from closing
   the store-lock descriptor. Create, release, role, or reaper callers can
   report refusal after authority already changed.
4. Snapshot verification revalidates the directory, marker, and witness but
   not every non-witness claim entry. A claim changed during validation can be
   accepted even though an immediate fresh snapshot differs.
5. The W0 `work status` claim workload and row collectors bypass the shared
   bounded canonical reader. Duplicate keys, unknown lifecycle status, or
   other integrity failures can be skipped and therefore hide active work.

## P2 findings

1. Strict JSON rejects explicit `NaN` and `Infinity` tokens but accepts a
   finite-looking exponent such as `1e9999` after it overflows to a non-finite
   Python float.
2. Sync still reports stale migration state or `applied=0` after a committed
   migration or write-then-error outcome. Apply-safe may return the pre-apply
   plan instead of the actual post-apply state.
3. Existing role-overlay idempotency validates the deterministic artifacts but
   still accepts a claim missing required stable metadata such as `team_id`.

## Stable signatures and prior knowledge

Exact canonical `compound_record search --no-legacy --json` returned `[]` for
the two newly normalized signatures:

- `defect:post-commit-fallible-step-reverses-durable-autho:cb20f7de91cd1390`;
- `defect:work-status-hides-active-claim-integrity-failure:f48114a15d1fee23`.

The snapshot race refines
`defect:claim-store-snapshot-accepts-stale-or-aliased-ba:165eeaa33e9e0650`;
exponent overflow refines
`defect:claim-json-accepts-nonfinite-or-duplicate-fields:2fc824544a55622d`;
sync reporting refines
`defect:sync-reports-zero-after-committed-claim-migratio:4317243460108472`;
and incomplete role metadata refines
`defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4`.
The parent-close and lock-close cases also recur under the already registered
post-commit publication/partial-transaction family. No prior Compound is
rewritten, and no new Compound is created before prevention and fresh Verify
evidence exist.

## Required disposition

Record RED tests before implementation. Return ownership identity from the
exclusive publisher without a post-commit path read; make only post-commit
cleanup close failures best effort; compare a final complete store snapshot;
route W0 through the canonical locked reader; reject every non-finite decoded
number; report sync's actual committed post-state; and define required stable
role metadata separately from intentionally mutable lifecycle fields. Then
rerun focused and full suites before Verify, Compound, and fresh W4.

## Residual boundary

The cooperative lock contract cannot protect against an uncooperative
same-user process that ignores the lock and replaces authority paths between
system calls. Mutable handoff/log append suffixes are also intentionally not
fully authenticated. These boundaries must be documented rather than claimed
as solved by this change.

## Safety boundary

Do not release the claim, dispatch external CI, mutate consumer repositories,
bump a version, tag, publish, push, deploy, or perform external release work.
