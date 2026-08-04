---
title: TASK-AR-648 Symbolic HEAD Lock Handoff P0 Replan
date: 2026-07-29
status: active
signal: block
severity: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
defect_signature: defect:claim-head-lock-handoff-can-miss-equal-oid-symbo:9711c2795ceafc89
reviewed_by: codex-root-p0-example-classifier
---

# TASK-AR-648 Symbolic HEAD Lock Handoff P0 Replan

## Decision

Keep Bean Wiki attempt 2, Allimbot, and release work stopped. The first
actual-`HEAD` reflog repair must not become a product commit or W4a candidate
because it releases Git's `HEAD.lock` before Runtime reacquires its own lock.

## Reproduction

The rejected design correctly validated the authorized symbolic ref in Git's
`reference-transaction prepared` hook, where Git owns the real
worktree-specific `HEAD.lock`. It also verified final ref and reflog state
after reacquiring that lock. An independent adversarial review found the
missing handoff invariant:

1. Git publishes the `HEAD` and branch transitions and removes its lock.
2. A concurrent normal Git symbolic-ref operation switches `A -> B -> A`
   between Git's unlock and Runtime's next `O_EXCL` lock.
3. The final symbolic ref, commit OID, and last claim reflog transition again
   equal the expected values.
4. A value-only postcondition can therefore return success without proving
   that the authorized symbolic `HEAD` survived the handoff.

The deterministic regression performs that equal-OID round trip immediately
before Runtime reacquires the lock. It must never run `post-commit` or return
`ok=true`.

## Remediation Contract

- Open the actual normal or linked-worktree symbolic `HEAD` regular file with
  `O_NOFOLLOW` before publication and retain the descriptor until the
  Runtime-owned post-publication lock is released.
- Bind its device, inode, link count, and exact symbolic-ref bytes into the
  private prepared-hook environment.
- Under Git's owned lock, validate the held identity and the exact two
  `HEAD`/branch transitions before and after delegating the configured
  `reference-transaction` hook.
- After Git returns, acquire the actual `HEAD.lock` with `O_EXCL`, then require
  the path's current identity to equal the still-open descriptor. Git's
  lockfile replacement makes an `A -> B -> A` round trip unlink or replace the
  held inode.
- Treat lock contention or any post-publication identity/state mismatch as
  terminal `ok=false`, `committed=true`,
  `publication_state=published_unverified`; skip `post-commit`, return
  non-zero at CLI/dispatcher boundaries, and explicitly forbid retry.
- Fail before ref publication on non-POSIX platforms or when `O_NOFOLLOW` is
  unavailable. Default working-tree claim persistence remains unchanged.
- State the cooperative threat boundary precisely: normal Git lockfile
  operations are covered; trusted same-authority hooks and arbitrary direct
  in-place writes to Git administrative files are not treated as hostile
  filesystem principals.

## Required Evidence

- Normal and linked-worktree actual `HEAD` plus branch reflog parity.
- Equal-OID switch-before-prepare, switch-after-publication, and
  final-state-preserving `A -> B -> A` regressions.
- Symlinked `HEAD`, missing `O_NOFOLLOW`, external lock, direct branch CAS,
  configured reference-hook veto/delegation, and Git-environment poisoning
  failures.
- A real dispatcher integration in which a committed reference hook performs
  the round trip: exactly one commit is published, the command returns
  non-zero with `created_published_unverified`, and no retry is performed.
- Root/template parity, current host lock, focused suites, full suite,
  sanitizer, Runtime asset usage, owner governance, fresh W4a, and a new
  independent W4b at one exact product SHA.

## Stop Boundary

Any success result after a Git lockfile rewrite, silent partial-publication
success, automatic retry, non-POSIX ref publication, hook bypass, consumer
worktree creation, release, version bump, tag, push, publish, deploy,
credential access, or network delivery remains release-blocking.
