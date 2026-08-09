---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-09-unit-task-ar-660-001-cross-platform-final-3
title: TASK-AR-660 Unit 001 Cross-Platform Final-3 Independent W4b
date: 2026-08-09
created_at: 2026-08-09T18:23:39+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
review_claim_id: CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-cross-platform-final-3
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
review_kind: w4b
reviewer: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-cross-platform-final-3
reviewer_role: independent-auditor
verifier_instance_id: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-cross-platform-final-3
worker_instance_id: le-20260809-130000-kst-ar660001
status: blocked
signal: block
score: 80
summary: The prepared-publication authority boundary is repaired on POSIX and fallback branches, but fallback parent rollback can delete a concurrently replaced empty directory after device/inode ABA reuse.
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
audited_commit: 7f0d3794d4cba31f221b3dbebc95e79ea6eb93d8
candidate_commit: 7f0d3794d4cba31f221b3dbebc95e79ea6eb93d8
candidate_tree: aa5d11983deb69fb6f8d8e0cf1dcef9408b0d098
accepted_baseline: 6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59
implementation_range: 6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59..7f0d3794d4cba31f221b3dbebc95e79ea6eb93d8
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_parent_identity_aba_repair_fresh_w4a_and_fresh_independent_w4b
w4a_ref: reviews/VERIFY-2026-08-09-unit-task-ar-660-001-20260809180817.json
t3_ref: reviews/REVIEW-2026-08-09-task-ar-660-unit001-cross-platform-publication-t3-replan.md
prior_w4b_ref: reviews/W4B-2026-08-09-unit-task-ar-660-001-authority-final-2.md
tags: [w4b, task-ar-660, recovery-receipt, atomic-io, cross-platform, parent-ownership, aba, revise]
---

# TASK-AR-660 Unit 001 cross-platform final-3 independent W4b

## Bottom line

`REVISE — P0: 0, P1: 1, P2: 0.`

The exact candidate
`7f0d3794d4cba31f221b3dbebc95e79ea6eb93d8` (tree
`aa5d11983deb69fb6f8d8e0cf1dcef9408b0d098`) repairs the prior W4b's
prepared-receipt authority window on every supported source branch. All nine
branch-forced non-POSIX operation/race combinations refuse after durable
sidecar preparation and leave the claim/store/event/receipt surfaces literally
unchanged, including receipt-root existence. The POSIX callback-rejection
rollback and ordinary atomic-parent cases also pass.

One blocking ownership defect remains. The fallback rollback token contains
only pathname, device, and inode. A rejected callback can delete and recreate
the operation-created empty parent; when the filesystem immediately reuses the
same device/inode, cleanup mistakes the replacement for its own directory and
removes it. This violates the T3 and Unit requirement that replaced directories
are preserved.

`w4b_acceptance: false`; `release_authorized: false`. Keep the main claim
claimed until the replacement ABA is repaired, a fresh W4a is committed, and a
different context-isolated W4b approves the new exact tree.

## P1 — Fallback parent rollback deletes an inode-reused replacement

`CreatedDirectoryIdentity` in `scripts/atomic_io.py` records only `path`,
`device`, and `inode`. `_rollback_created_parents()` at lines 336-365 performs
an `lstat()`, checks only directory type plus `(st_dev, st_ino)`, and then calls
`rmdir()`. This is not a generation-stable ownership proof: a removed directory
can be recreated at the same pathname with the same reused inode before
rollback.

An independent exact-tree probe selected the fallback/Windows publisher while
delegating filesystem calls to the audit host. After the durable sidecar was
visible, the callback:

1. recorded the operation-created parent inode;
2. removed the owned sidecar and parent;
3. created a distinct empty replacement at the same pathname with mode `0711`;
4. confirmed the replacement existed; and
5. rejected publication.

The host reused the inode on the first attempt, and the candidate deleted the
replacement:

```text
attempt 0
created_inode=19962160
replacement_inode=19962160
replacement_mode=0o711
replacement_existed_before_cleanup=True
replacement_exists_after_cleanup=False
```

The callback ran once and its exception propagated, so this is specifically the
ownership cleanup, not publication or test-harness behavior. A second probe
also showed that replacing an operation-created ancestor with a symlink back to
the moved tree lets the absolute-path cleanup traverse that alias and remove an
owned descendant at the displaced location. The latter does not remove a
nonempty directory, but confirms that rollback does not revalidate the full
direct ancestor chain.

This is P1 because callback rejection is supposed to be a fail-closed,
ownership-bounded rollback. Deleting another creator's replacement namespace is
an unauthorized concurrent mutation on the newly added cross-platform recovery
path. The current distinct-inode regression cannot detect the ABA because it
asserts that the replacement inode differs.

Required repair: retain a non-reusable ownership authority across callback and
cleanup (for example a pinned directory handle where the platform supports it),
and use a generation-stable replacement check plus full direct/non-alias
ancestor validation on fallback platforms. Add a deterministic regression that
recreates an empty parent with the same reported device/inode and proves it is
preserved. Do not weaken the existing leaf-first, pre-existing, and nonempty
preservation cases.

## Cross-platform publication boundary — pass

Static inspection places the callback at the final pre-publication boundary on
all supported exclusive paths:

- pinned POSIX atomic publisher: callback immediately precedes `os.link()` at
  `scripts/atomic_io.py:472-475`;
- Windows fallback publisher: final `_fallback_prepare_parent()` completes,
  then callback immediately precedes `os.rename()` at lines 488-495;
- non-Windows fallback publisher: callback immediately precedes `os.link()` at
  lines 507-510;
- pinned POSIX receipt publisher: durable write/fsync/close and sidecar identity
  re-stat complete before callback immediately precedes `os.link()` at
  `scripts/recovery_receipt.py:750-773`; and
- the recovery fallback forwards `precommit` into strict exclusive
  `publish_json_atomic()` at lines 940-950 instead of proving authority in its
  caller.

There is no fallible preparation or validation between the callback and the
destination link/rename. Overwrite APIs retain their old contract and do not
expose the callback.

The independent branch-forced non-POSIX matrix selected both
`recovery_receipt`'s fallback path and `atomic_io`'s Windows branch. Damage was
injected with the prepared sidecar already present and before the publisher's
callback. This was source-branch emulation on POSIX, not a native Windows run:

```text
adopt/disappearance          rc=1 sidecar=True literal_unchanged=True root_unchanged=True
adopt/replacement            rc=1 sidecar=True literal_unchanged=True root_unchanged=True
adopt/field-drift            rc=1 sidecar=True literal_unchanged=True root_unchanged=True
terminalize/disappearance    rc=1 sidecar=True literal_unchanged=True root_unchanged=True
terminalize/replacement      rc=1 sidecar=True literal_unchanged=True root_unchanged=True
terminalize/field-drift      rc=1 sidecar=True literal_unchanged=True root_unchanged=True
activate-store/disappearance rc=1 sidecar=True literal_unchanged=True root_unchanged=True
activate-store/replacement   rc=1 sidecar=True literal_unchanged=True root_unchanged=True
activate-store/field-drift   rc=1 sidecar=True literal_unchanged=True root_unchanged=True
```

Each case preserved exact claim bytes/tree entries, claim-store admin entries,
pane-event bytes, receipt entries, and the receipt root's existence bit.

## POSIX rollback and ordinary atomic ownership — pass

An independent POSIX receipt probe observed the durable sidecar inside the
callback, rejected once, and confirmed that the complete newly created nested
parent tree and receipt root were absent afterward.

Independent fallback probes also confirmed:

- nested operation-created empty parents are removed leaf-first;
- pre-existing parents are preserved;
- concurrently populated parents and their foreign bytes are preserved;
- an empty replacement with a distinct inode is preserved;
- callback success followed by destination failure invokes the callback exactly
  once, does not retry it, and does not roll back the created parent;
- successful callback plus publication invokes the callback exactly once; and
- a Windows absent-destination rename failure propagates the exact original
  `OSError` object, not a synthesized `FileExistsError`.

These passes do not discharge the same-inode replacement ABA above.

## Exact suites and W4a freshness

The fresh committed W4a reports `768 passed, 6 skipped` and `36 passed`. From a
detached exact-commit clone, the verifier independently repeated the two exact
Unit commands:

```text
PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_claim_reaper.py tests/test_task_claim_dispatcher.py tests/test_attribution_gate.py tests/test_role_routing.py -q
768 passed, 6 skipped in 139.25s

PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
36 passed in 20.19s
```

Repair commit `c90edd3faf71e8d95e739521dc6671516abe802e` is followed only by
Unit/plan/index/W4a evidence in candidate commit `7f0d3794`; no production or
test code changes occur after W4a.

## Parity, receipts, provenance, and work identity

- `git diff --check` passes for the complete baseline range.
- `recovery_receipt.py --check` passes.
- `template_mirror_gate.py --check` reports `expected=87`, `common=87`,
  `identical=84`, `intentional=3`, `findings=0`.
- Direct byte comparisons pass for all modified runtime/schema mirror groups,
  including dispatcher, role routing, atomic I/O, reaper/hook, pane events,
  recovery receipt, attribution, schema, and all three claim-store copies.
- `regen_host_lock_if_needed.py --check` reports the managed fixture lock is up
  to date.
- Scoped taskset-work, agent-identity, task-identity, and plan-assumption gates
  pass with zero findings. Attribution passes with zero block findings; its
  historical watch findings remain nonblocking.
- The four recovery receipt SHA-256 values remain
  `550edb5bcafece81...`, `edace69d36e162b8...`,
  `5a1b79d4998173da...`, and `f13a14092ce28dbb...`.
- Receipts and pane events 668/669 preserve Owner identity exactly as
  `ycpiglet <68498184+ycpiglet@users.noreply.github.com>`. Event actor, role,
  display name, callsite, and instance ID match
  `le-20260809-130000-kst-ar660001.json` exactly.
- An independent canonical-JSON oracle recomputed the main claim's task and
  unit identity components as `96740ab993028195...` and
  `c5184c06c2efca5c...`; their binding digest is
  `8dd1d23efa72b195...`, exactly matching the persisted claim. The canonical
  UUIDs are task `d74673e9-5820-495a-8f10-6fd1f2e96e8a` and unit
  `1807fd98-34ea-4bd6-b4eb-a29e4e35ada4`.

## Historical AR-655 recovery invariant

Historical `CLAIM-20260803-002651-task-ar-655-5f27` remains exactly `expired`.
It is not deleted, completed, or released. Its claim, handoff, log, and Owner
recovery record are byte-identical to accepted baseline
`6c1f67f4c52c193e10236fc9ced1cc5eb53a4a59`, with SHA-256 values:

```text
claim   42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5
handoff 72c02cf97d7b105e7306d827ec1acb4279c380ad76f3f729a4f866d7801dcb7f
log     21281f4b1974744072874057aea84f425bb41e3f5b21ab7936a9c4a0f4637f29
record  d5883c05ecf467dcc01e2e31848c550a2d4305fa9f5df0b5d5652555ae0450b3
```

The preserved Owner recovery record retains before digest
`96f7d3d505cd9774e136f3a1bdc3e2c270b2c2aa11a299f6f6e04ddeb9cd59c1`,
after digest `42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5`,
Owner recovery attribution, and the explicit statement that the claim was
terminalized only to `expired`.

## Complete-range and independence statement

The accepted-baseline range contains 67 changed paths, 17,398 insertions, and
1,501 deletions. The complete range, Unit record, latest T3 replan, fresh W4a,
prior independent W4b, production mirror pairs, managed lock, claims, receipts,
events, and historical recovery artifacts were reviewed.

The verifier instance
`independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-cross-platform-final-3`
is different from worker `le-20260809-130000-kst-ar660001` and received no
worker conversation. Candidate inspection and execution used detached clone
`/tmp/ar660-w4b-final3.VuuoKk/repo`, pinned to the exact candidate commit and
tree. Uncommitted live-worktree reviewer bootstrap overlays were not read as
candidate evidence.

This review file is the verifier's only repository write. No code, test, task,
unit, plan, index, claim, instance, event, lock, receipt, or historical artifact
was modified; nothing was staged, committed, released, merged, pushed, tagged,
published, or deployed.

## Decision and claim disposition

Do not accept, close, merge, or release Unit 001 or
`CLAIM-20260809-125520-task-ar-660-491d`. Repair the fallback parent-identity
ABA so every replaced empty directory is preserved, add a deterministic
same-identity replacement regression, regenerate mirror/lock artifacts as
needed, commit a fresh W4a, and assign a new context-isolated W4b.

This evidence grants no release, commit, merge, push, tag, publish, deploy,
external-CI, rotation, or consumer-mutation authority.
