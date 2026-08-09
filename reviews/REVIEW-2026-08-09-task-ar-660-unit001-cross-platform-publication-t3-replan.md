---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-cross-platform-publication-t3-replan
title: TASK-AR-660 Unit 001 Cross-Platform Receipt Publication T3 Replan
date: 2026-08-09
created_at: 2026-08-09T17:50:00+09:00
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
verdict: AMEND_CROSS_PLATFORM_PUBLICATION_BOUNDARY_AND_EMPTY_PARENT_ROLLBACK
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, recovery-receipt, atomic-io, non-posix, toctou]
---

# TASK-AR-660 Unit 001 cross-platform receipt publication T3 replan

## Bottom Line

Reopen Unit 001 after the final-2 independent W4b. Put the external recovery
authority callback inside the exclusive atomic publisher on every supported
platform, after durable sidecar preparation and immediately before destination
publication. A rejected callback must also restore the exact pre-call parent
tree, including whether the receipt root existed.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| POSIX publication boundary | pass | sidecar fsync and identity proof precede the callback; `os.link` immediately follows it |
| Non-POSIX publication boundary | block | `reviews/W4B-2026-08-09-unit-task-ar-660-001-authority-final-2.md` proves the callback runs before atomic sidecar preparation |
| Rejected-proof cleanup | revise | a newly created empty receipt directory survives even though no receipt authority remains |
| Declared footprint | pass | Unit 001 and claim scope already include root/template `atomic_io.py`, `recovery_receipt.py`, and their tests |

## Action

Keep the current target-file footprint. Extend only the exclusive publish API
with an optional no-argument precommit callback. Thread it through the JSON and
text publish entry points into the destination publisher. Invoke it exactly
once, after the sidecar has been written, flushed, fsynced under the requested
policy, closed, and identified, and after the final fallback parent validation,
with no fallible preparation step between the callback and the destination
link or rename. Overwrite APIs retain their existing contract and do not accept
the callback.

Track each parent directory created by the active atomic operation at the
successful `mkdir` boundary, together with its device and inode. If and only if
the callback rejects, remove those owned directories in reverse order using an
empty-directory operation after revalidating the same direct, non-alias
identity. Never remove a pre-existing, replaced, or nonempty directory. Reuse
the same ownership-aware cleanup for the pinned POSIX receipt publisher so
callback rejection restores both receipt entries and root existence.

Add RED coverage for:

1. exclusive publisher ordering and exactly-once callback invocation on the
   fallback/non-POSIX branch;
2. callback rejection after sidecar preparation leaving destination, sidecars,
   and every operation-created parent absent;
3. pre-existing and concurrently populated parents never being removed;
4. adopt, terminalize, and activate-store against actor disappearance,
   identical-byte inode replacement, and canonical field drift at the fallback
   destination boundary; and
5. receipt-root existence plus entry snapshots, not an entry-only snapshot.

Mirror production runtime files byte-for-byte, regenerate the managed host
lock, and repeat the complete Unit verification and template suites.

## Risks / Blockers

Calling the callback in `_write_text()` immediately before `_publish_sidecar()`
is insufficient if `_publish_sidecar()` then performs fallback parent
validation. The callback belongs after that validation and immediately before
the actual destination operation. Cleanup based only on a pre-call
`Path.exists()` check is also insufficient because a concurrent creator could
win the missing-parent race; successful `mkdir` ownership plus device/inode
revalidation is required.

The Windows exclusive path performs one destination rename rather than the
overwrite retry loop, so the callback must run once immediately before that
rename. A publication error after a successful callback remains an ordinary
pre-commit publication failure; the callback is not retried.

## Decision

`ACCEPT` this bounded correction. Reset Unit 001 verification to pending,
re-record taskset assumptions against this design record, and renew the main
claim with exact revision, worker, callsite, and old scope digest CAS before
implementation. Preserve the existing work-identity binding.

This decision grants no Unit 002 rotation work, main-claim release before a
fresh W4b approval, task completion, external CI, consumer mutation, push,
tag, publish, or deploy authority.

## Next Steps

Commit RED tests before production changes, implement root/template parity,
regenerate the host lock, run fresh W4a, and dispatch a new context-isolated
W4b. Release the Unit 001 claim only if that review returns `APPROVE` with
P0/P1 zero.
