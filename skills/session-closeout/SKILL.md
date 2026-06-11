---
name: session-closeout
description: Use when the Owner says 마무리, 정리, closeout, cleanup, or asks whether stash, branch, PR, issue, worktree, archive, or dirty state remains.
---

# Session Closeout

## Required Sequence

1. Capture current `git status -sb`, `git stash list`, `git worktree list --porcelain`, and active branch scan.
2. Separate declared current work from late dirty work.
3. For declared work, commit, PR, merge, and sync `main` only when Owner policy allows those side effects.
4. For late dirty work, preserve with stash and archive ref before dropping local state.
5. Create or update an issue with every archive ref that replaces local state.
6. Delete only active work branches that have been merged or archived.
7. Final claim requires clean `git status -sb`, empty stash list, root-only worktree list, and documented residual archive refs.

## Parallel Session Closeout

- Treat parallel-session closeout as the same sequence with an added ownership
  check: only close the branch/worktree for the declared taskset.
- Do not repoint unrelated active panes just to make the current taskset look
  active.
- Preserve unrelated dirty files, branches, claims, and worktrees for their
  owning pane.
