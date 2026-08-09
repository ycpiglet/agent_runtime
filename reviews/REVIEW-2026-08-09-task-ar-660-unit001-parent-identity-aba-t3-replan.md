---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-parent-identity-aba-t3-replan
title: TASK-AR-660 Unit 001 Parent Identity ABA T3 Replan
date: 2026-08-09
created_at: 2026-08-09T18:31:00+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
tier: T3
reviewer: le-20260809-130000-kst-ar660001
reviewer_role: orchestrator
status: accepted
signal: pass
score: 100
verdict: AMEND_PARENT_OWNERSHIP_TO_REJECT_IDENTITY_ABA_AND_ANCESTOR_ALIASING
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, atomic-io, parent-ownership, aba, non-posix]
---

# TASK-AR-660 Unit 001 parent identity ABA T3 replan

## Bottom Line

Reopen Unit 001 after the cross-platform final-3 W4b. Device and inode alone
are not a durable ownership generation: an empty directory can be deleted and
recreated at the same pathname with the same immediately reused inode. Cleanup
must preserve that replacement and must not traverse an ancestor alias to find
the displaced original tree.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| Prepared-publication authority | pass | all three recovery operations and all three actor-drift shapes refuse at the final fallback boundary |
| Literal callback-rejection rollback | pass for stable trees | newly created empty receipt roots are removed when ownership remains intact |
| Same-inode replacement | block | `reviews/W4B-2026-08-09-unit-task-ar-660-001-cross-platform-final-3.md` reproduced immediate inode reuse and deletion of the replacement |
| Ancestor alias replacement | block | the same audit showed path cleanup can traverse a new symlink into the displaced owned tree |
| Declared footprint | pass | Unit 001 already owns root/template `atomic_io.py`, `recovery_receipt.py`, and their tests |

## Action

Retain a callback-bound ownership generation for every operation-created
directory and a direct/non-alias snapshot of the complete parent chain. Capture
it only after the final parent validation and sidecar preparation, immediately
before the external callback. The generation must contain more than
`(device, inode)`: include immutable type/attribute evidence and a change or
birth-time generation value where the platform exposes it.

On callback rejection, validate the complete direct parent chain and the exact
prepared sidecar identity before unlinking any pathname. If a created
directory, ancestor, or sidecar is missing, aliased, replaced, or generation
different, cleanup loses authority and must preserve the replacement tree.
Never refresh a changed post-callback pathname and then call it owned. Only an
intact callback-bound generation may authorize sidecar cleanup and leaf-first
empty-directory removal.

The stable-tree case must retain its current literal rollback: remove the exact
owned sidecar and then the operation-created empty directories leaf-first.
Pre-existing, concurrently populated, replaced, same-device/inode-reused, and
ancestor-aliased trees are preserved. A successful callback followed by
publication failure still invokes the callback once and does not use the
callback-rejection rollback path.

Add RED coverage for:

1. a deterministic replacement whose reported device/inode collides with the
   callback-bound directory but whose generation is distinct;
2. real immediate inode reuse when supported by the test filesystem;
3. an operation-created ancestor replaced by a symlink to the displaced tree;
4. exact stable-tree rollback, pre-existing and nonempty preservation, and
   callback exactly-once behavior; and
5. root/template parity plus managed host-lock freshness.

## Risks / Blockers

Checking mode alone is insufficient because a replacement can use the same
permissions. Checking a timestamp captured at `mkdir` is also insufficient
because this operation's own sidecar creation changes parent metadata. The
generation must be captured at the final pre-callback boundary, and it must be
validated before this operation unlinks its sidecar and changes the directory
again.

Fallback path validation cannot claim cryptographic ownership. Its contract is
conservative local-filesystem cleanup: uncertainty forfeits deletion authority.
The repair must prefer a harmless owned-sidecar leak under adversarial path
replacement over deleting or traversing another creator's namespace.

## Decision

`ACCEPT` this bounded correction. Reset Unit 001 verification to pending,
re-record taskset assumptions against this design record, and renew the main
claim using exact revision, worker, callsite, and scope-digest CAS before
implementation. Preserve the current work-identity binding and target-file
footprint.

This decision grants no Unit 002 work, main-claim release, acceptance,
completion, external CI, consumer mutation, push, tag, publish, or deploy
authority.

## Next Steps

Commit deterministic RED tests before production changes, repair the
generation-stable cleanup in root and template together, regenerate the host
lock, run a fresh W4a, and dispatch a new context-isolated W4b against the exact
new candidate.
