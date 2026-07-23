---
id: RELEASE-READINESS-2026-07-23-v0.7.0-CLOSEOUT
title: v0.7.0 release closeout readiness
kind: release-readiness
status: pass
date: 2026-07-23
version: 0.7.0
decision: closeout_pr_go
score: 96
---

# v0.7.0 release closeout readiness

## Current objective

Integrate the completed release evidence and W6 project state, then remove the
transient branch/worktree after exact-head and post-merge CI pass.

## Current state

- Release: public, non-draft, non-prerelease at
  `https://github.com/ycpiglet/agent_runtime/releases/tag/v0.7.0`.
- Annotated tag object: `99292aadd72284b83f6e55b1de4e48102f449512`.
- Peeled release commit: `23c4be4059dc4c12d107ac8cc5fefa795dfab7f8`.
- TASK-AR-602 task/unit: completed with passing, work-id-specific W4a evidence.
- Named taskset completion gate: pass, findings 0.
- Active claims: 0. The closeout branch/worktree remains until PR integration.

## Completed since candidate readiness

- PR #342 and merged-main CI runs `29980218065` and `29980353636` passed
  Python 3.10, 3.11, and 3.12.
- GitHub release body exactly matched the reviewed 1,826-character notes file.
- All seven intake issues are closed.
- Unit W4a and task W4a each passed 2,198 tests with 6 skips and no failures.
- Technical W4b approved release integrity 98/100; the skeptical path identified
  provenance loss, then approved closeout 96/100 after exact repair and T3
  revalidation.
- Released claim metadata for this taskset was normalized to
  `phase=taskset-completed`, `progress_pct=100`; all taskset claims are released.

## Open decisions

- TASK-AR-621: define cross-platform work-verify command execution so Windows
  shell metacharacters cannot silently change registered commands.
- TASK-AR-622: implement fail-closed handling or explicitly reviewed migration
  for unsafe legacy raw frontmatter scalars. Its T3 assumption gate is current.

## Blockers and risks

- Release blocker: none.
- Closeout integration blocker: exact-head closeout PR CI and post-merge CI must
  pass before worktree/branch removal.
- The annotated tag is unsigned, consistent with the repository's existing tag
  contract. Four Python deprecation warnings remain non-blocking.
- A global collaboration-governance scan still reports historical lifecycle
  watches outside this taskset; it reports zero block findings.

## Artifacts and paths

- `reviews/RELEASE-NOTES-2026-07-23-v0.7.0.md`
- `reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723142627.json`
- `reviews/VERIFY-2026-07-23-task-ar-602-20260723143848.json`
- `reviews/W4B-2026-07-23-TASK-AR-602-FINAL.md`
- `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK-2.md`
- `reviews/REVIEW-2026-07-23-task-ar-622-t3-legacy-scalar-replan.md`

## Next actions

1. Push the closeout branch and open the closeout PR.
2. Require exact-head Python 3.10/3.11/3.12 success, merge, and require the
   merged-main matrix to pass.
3. Remove the merged worktree and local/remote branch, then run W0 and confirm
   one main worktree, zero active claims, and zero divergent tasks.

## Rollback and forward-fix

- Pre-merge closeout evidence can be abandoned without changing the published
  release.
- After merge, revert only the closeout metadata through a PR if necessary.
- Never move or silently delete published `v0.7.0`; publish a warning and
  forward-fix as `v0.7.1`. Prior immutable release: `v0.6.0`.

