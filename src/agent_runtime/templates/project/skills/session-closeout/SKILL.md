---
name: session-closeout
version: 1.0.0
description: Use when the Owner says 마무리, 정리, closeout, cleanup, or asks whether stash, branch, PR, issue, worktree, archive, or dirty state remains.
triggers:
  - 마무리
  - 정리
  - closeout
  - cleanup
dependencies:
  - scripts/session_baseline.py
  - scripts/dirty_intake.py
  - scripts/taskset_work_gate.py
registry_id: session-closeout
template_path: src/agent_runtime/templates/project/skills/session-closeout/SKILL.md
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
