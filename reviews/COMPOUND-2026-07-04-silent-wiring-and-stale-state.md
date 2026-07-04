---
type: compound
title: Silent cross-step wiring failures + stale open-state debt (autonomous loop session)
date: 2026-07-04
status: recorded
signal: pass
source_session: d1f5743f-0ecd-43de-b1e2-b31c6d988bdc
casebook: agents/project/casebooks/failure-and-compound-casebook.md
related: [PR #238, PR #239, PR #240, PR #242, PR #243, issue #211, issue #241, issue #125, issue #162, issue #237]
---

# Silent cross-step wiring failures + stale open-state compound

One autonomous find-verify-fix loop (2026-07-04) surfaced two recurring
failure families. Both already had near-miss precedents in this casebook;
this note records the generalized lessons and prevention routes.

## What happened, and why

1. **A green pipeline whose product never existed.** `release-auto.yml`'s
   notify + Owner-approval-issue steps read `.tmp/release-auto-result.json`,
   produced by `python … | tee .tmp/release-auto-result.json`. `.tmp/` is
   gitignored, so it never exists in a fresh CI checkout; `tee` failed to
   create the file, `rc=${PIPESTATUS[0]}` deliberately captured only python's
   exit code, and every notify step skipped with "no orchestrator result
   file" — while every step stayed green. Net effect: the proactive Owner
   notification added by PR #210 **never fired once in CI**, and a pending
   v0.6.0 minor release sat unnoticed from 2026-06-29 (run 28353042537)
   until this session opened issue #241 by hand. **Root cause: a cross-step
   file contract that no test asserted; "steps are green" was read as "the
   notification works."** Fix: PR #240 (mkdir + loud failure when the result
   file is missing + a workflow contract test that pins mkdir-before-tee).
   (`silent-cross-step-wiring`)

2. **Verified-done work left open everywhere.** The live board showed
   TASK-AR-585/586 as the only open work, but both had been fully delivered
   weeks earlier by the release-automation lane (PR #183/#210 era) under
   different task framing. Issues #20/#21 (bugs fixed with regression guards
   via TASK-AR-532/PR #144), #131 (intake pipeline shipped 7/7), and #211
   (fixed this session) were all open with zero remaining work. Meanwhile
   the *genuinely* unlanded work was invisible: the beta-tester role
   strengthening sat in a dirty-work archive stash (#162, recovered via PR
   #242) and a crash-recovery branch was archived unmerged but fully
   superseded (#237, closed as no-restore). **Root cause: closure requires a
   verifying agent to walk open state against merged reality, and nothing in
   the loop is assigned that sweep.** This session did it manually: verify
   acceptance criteria against main, then close with evidence, or recover
   what actually never landed. (`stale-open-state-debt`)

## Reusable lessons

- When a workflow writes a file in one step and reads it in another, the
  existence of that file is a **contract**: pin it with (a) a loud in-step
  failure when the artifact is missing and (b) a repo test asserting the
  wiring (creation precedes consumption). "All steps green" proves nothing
  about side-channel products, and `PIPESTATUS`-style rc-forwarding
  actively hides plumbing failures.
- Notification paths deserve end-to-end evidence, not code review: the #210
  notification was reviewed, merged, and believed working for 11 days. The
  first real proof is a created/updated GitHub issue — check for the
  artifact, not the code.
- Open state (issues, board tasks, archive stashes) drifts from merged
  reality within weeks under high merge velocity. A periodic sweep that
  diffs open items against main — closing with evidence or recovering
  unlanded content — is cheap (this one closed 7 issues/tasks and recovered
  one real feature) and keeps the board a trustworthy attention surface.

## Addendum (same day, later cycle): query failure read as "no data"

3. **A transient git failure silently skipped a release cycle.** The
   cadence trigger's `_git` helper folded *"the spawn failed after
   retries"* and *"git answered non-zero"* into the same `None`. A loaded
   runner killed one spawn, `rev-list` returned no answer, commits
   collapsed to 0, and `release_auto_noncritical` reported `not-triggered`
   with exit 0 — indistinguishable from a genuinely quiet repo. Surfaced
   only as an assertion flake on main CI (run 28680340240,
   `test_major_or_breaking_flag_halts`), with zero diagnostics. **Root
   cause: a fail-open default in a decision path — "could not ask" must
   never be classified as "no data."** Fix: PR #254 (query-error ledger in
   the trigger, `git-query-error` report status, `RESULT_TRIGGER_ERROR`
   exit 5, signal-death retried) + PR #255 (workflow fails the run red on
   rc=5; notify steps still run via `if: always()`).
   (`silent-query-error-as-no-data`)

## Feed-forward

- Casebook rows added: `silent-cross-step-wiring`, `stale-open-state-debt`,
  `silent-query-error-as-no-data`.
- Proposal (not implemented): a scheduled "open-state sweep" checklist or
  gate that lists open issues/board tasks whose referenced acceptance
  criteria already hold on main.
