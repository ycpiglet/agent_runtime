---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-09-unit-task-ar-660-001-generation-final-4
title: TASK-AR-660 Unit 001 Generation Final-4 Independent W4b
date: 2026-08-09
created_at: 2026-08-09T20:18:25+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
review_claim_id: CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-generation-final-4
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
review_kind: w4b
reviewer: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-generation-final-4
reviewer_role: independent-auditor
verifier_instance_id: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-generation-final-4
worker_instance_id: le-20260809-130000-kst-ar660001
status: blocked
signal: block
score: 80
summary: Callback-complete generation checks are present, but fallback rollback can delete a directory replaced before the callback snapshot when the replacement reports the created directory's device and inode with a different generation.
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
audited_commit: e57c679f5aef687f54bec3785033b079d9c3f6df
candidate_commit: e57c679f5aef687f54bec3785033b079d9c3f6df
candidate_tree: 9cb4a2d9bc2607fcf974d682af1b5f527d4786f4
implementation_commit: a992195995108b6f14cc890792b900e51025ad95
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_created_directory_generation_repair_fresh_w4a_and_fresh_independent_w4b
w4a_ref: reviews/VERIFY-2026-08-09-unit-task-ar-660-001-20260809194149.json
prior_w4b_ref: reviews/W4B-2026-08-09-unit-task-ar-660-001-cross-platform-final-3.md
t3_refs:
  - reviews/REVIEW-2026-08-09-task-ar-660-unit001-cross-platform-publication-t3-replan.md
  - reviews/REVIEW-2026-08-09-task-ar-660-unit001-parent-identity-aba-t3-replan.md
  - reviews/REVIEW-2026-08-09-task-ar-660-unit001-cleanup-concurrency-boundary-t3-replan.md
tags: [w4b, task-ar-660, recovery-receipt, atomic-io, generation, windows-fallback, aba, revise]
---

# TASK-AR-660 Unit 001 generation final-4 independent W4b

## Bottom line

`REVISE — P0: 0, P1: 1, P2: 0.`

The exact candidate
`e57c679f5aef687f54bec3785033b079d9c3f6df` (tree
`9cb4a2d9bc2607fcf974d682af1b5f527d4786f4`) passes both registered Unit
suites, template/host-lock parity, the scoped T3 assumption gate, receipt
validation, work-identity validation, and historical-claim preservation.

One blocking cleanup-authority defect remains. `CreatedDirectoryIdentity`
retains only `(path, device, inode)`. If a fallback-created directory is
replaced after creation but before `_capture_precommit_cleanup()` takes its
callback-bound snapshot, and the replacement reports the same device/inode
with a different generation, that snapshot records the replacement's new
generation. Callback rejection then validates that new generation as stable,
unlinks the sidecar, and `_rollback_created_parents()` authorizes `rmdir()` from
the old three-field token. The replacement is removed. This violates the Unit
acceptance requirement to preserve same-device/inode-reused replacements.

`w4b_acceptance: false`; `release_authorized: false`.

## P1 — Created-directory ownership loses the pre-snapshot generation

`scripts/atomic_io.py:95-100` defines `CreatedDirectoryIdentity` with only
`path`, `device`, and `inode`; the fallback creation path stores exactly those
fields at lines 545-551. The later callback proof has a full
`_CleanupPathIdentity`, but it describes whatever occupies the pathname at the
snapshot boundary. No full-generation comparison binds that object back to the
directory created by this operation. At lines 623-634, rollback compares the
proof's leaf to the creation token using only device/inode and calls `rmdir()`.

An isolated deterministic probe selected the modeled Windows fallback branch.
Immediately before the real callback snapshot, it moved the exact prepared
sidecar through a hard link, replaced the operation-created parent, and made
the replacement metadata report the created parent's device/inode with a
different birth/change generation. The callback then rejected, and no writer
raced the post-callback cleanup:

```text
modeled_platform=windows-fallback
callback_calls=1
created_dev_ino=(66306, 19700490)
replacement_reported_dev_ino=(66306, 19700490)
created_generation=1786274173670945307
replacement_generation=1786274174670945307
replacement_preserved=False
```

The exact callback exception propagated and the replacement parent was absent
after rejection. This is not the concurrency-boundary exclusion for an
arbitrary writer racing after final validation: the replacement was complete
before the callback snapshot, and the namespace remained quiescent throughout
rejection cleanup.

The current regression at `tests/test_atomic_io.py:530` changes the parent
during the callback, after the proof has captured the original generation, so
the full callback-complete comparison correctly preserves that replacement.
The sidecar reuse regression at line 774 also binds the opened sidecar, not the
created parent. Neither covers replacement between fallback creation and the
callback snapshot.

Required correction: carry sufficient generation/object evidence for each
operation-created directory into the callback-bound proof, and refuse both
sidecar and parent cleanup when the callback snapshot cannot be tied back to
that created object. Add a deterministic pre-snapshot same-device/inode,
different-generation replacement regression for the fallback branch. Preserve
the existing stable-tree rollback and conservative behavior for missing,
aliased, changed, populated, and callback-time replacements.

## Registered verification

Both commands were run from a clean detached copy of the exact candidate:

```text
PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_claim_reaper.py tests/test_task_claim_dispatcher.py tests/test_attribution_gate.py tests/test_role_routing.py -q
778 passed, 6 skipped in 139.97s

PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
36 passed in 20.06s
```

The committed W4a record reports the same counts (`778 passed, 6 skipped` and
`36 passed`). Candidate commit `e57c679f` changes only the Unit, plan
assumptions, review index, and W4a JSON relative to implementation commit
`a9921959`; there is no post-W4a product or test change.

## T3 boundary assessment

- Cross-platform publication timing passes static and test inspection. The
  exclusive callback runs once after sidecar preparation and final fallback
  parent validation, immediately before the destination link or rename.
- Stable-tree callback rejection, pre-existing/nonempty preservation,
  callback-time generation changes, sidecar generation changes, and ancestor
  alias replacement are covered and pass.
- The cleanup-concurrency clarification does not excuse this finding. The
  probe uses a quiescent post-callback interval and makes no native
  compare-delete claim against a racing noncooperating writer.
- The parent-identity ABA T3 boundary is not met because the creation token
  cannot distinguish the created directory from a pre-snapshot replacement.
  Capturing a full generation only after replacement makes the replacement
  look authoritative rather than proving creation ownership.
- Windows conclusions are source-branch models on the POSIX audit host, not
  native-Windows evidence. The modeled behavior is sufficient to establish
  the control-flow defect; native Windows remains subject to the Unit's stated
  evidence boundary.

## Other inspected surfaces

- Template mirror gate: `expected=87`, `common=87`, `identical=84`,
  `intentional=3`, `findings=0`. Direct comparisons pass for every declared
  runtime/schema mirror group, including all three claim-store copies.
- `python scripts/regen_host_lock_if_needed.py --check` passes. Relevant lock
  entries are managed and match their template hashes.
- `python scripts/plan_assumption_gate.py --check --taskset
  TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION` passes with zero
  findings. The current snapshot records 41 exact anchors and the accepted
  cleanup-concurrency T3 design record.
- `python scripts/taskset_work_gate.py --root . --check --task-set-id
  TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION` and
  `python scripts/task_identity.py --root . check` pass with zero findings.
- `PYTHONPATH=scripts python scripts/recovery_receipt.py --root . --check`
  passes. Prepared/committed receipt self-digests and exact transition hashes
  validate; receipt-first, subject-failure, activation no-op, terminal truth,
  and callback timing behavior are exercised by the registered suite.
- The main claim's canonical work binding validates against task UUID
  `d74673e9-5820-495a-8f10-6fd1f2e96e8a`, unit UUID
  `1807fd98-34ea-4bd6-b4eb-a29e4e35ada4`, and binding digest
  `8dd1d23efa72b195e6bd36c0cf4ead0c6e8f179543da484abc2f8f4958ddd2ad`.
  Display-ID collisions and canonical UUID drift fail closed in the registered
  mutation tests.
- Post-cutoff pane-event attribution tests reject absent or canonically
  mismatched instances. The repository attribution gate reports zero blocking
  findings; historical watch findings remain nonblocking.
- Historical `CLAIM-20260803-002651-task-ar-655-5f27` remains `expired` with
  SHA-256 `42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5`.
  It has no synthesized recovery receipt and was not deleted, completed,
  released, or rewritten.
- The complete scoped range is whitespace-clean. Every changed
  production/schema/test path is registered by Unit 001; root/template parity,
  host-lock ownership, and plan assumptions are current.

## Independence and repository boundary

The verifier identity
`independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-generation-final-4`
is distinct from worker `le-20260809-130000-kst-ar660001`. Inspection and test
execution used detached clone
`/tmp/task-ar-660-generation-final-4.gJf97y/repo`; live claim overlay files were
not candidate evidence.

This report is the verifier's only live-repository write. No code, test, Unit,
plan, index, claim, instance, event, receipt, lock, or historical artifact was
modified; nothing was staged, committed, released, merged, pushed, tagged,
published, or deployed.

## Decision

Do not accept, close, merge, or release Unit 001 or its primary claim. Repair
the created-directory generation binding, add the pre-snapshot regression,
regenerate mirrors/lock if needed, record fresh W4a evidence, and obtain a new
context-isolated W4b on the corrected exact tree.
