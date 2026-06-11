# Session Closeout Contract

## Purpose

Session closeout prevents false clean claims by separating baseline state, current dirty work, preserved archives, active branches, worktrees, stashes, and issue handoff records.

## Owner Meaning

When the Owner says "마무리", "정리", "cleanup", or "closeout", the agent must treat local git state, task records, Owner docs, branch/worktree residue, stash/archive refs, and issue pointers as part of the requested work.

## Rules

- Record a baseline at SessionStart before task work.
- Treat `main` checkout as orchestrator-owned during parallel work.
- Classify dirty work before mutating it.
- Preserve unknown or late dirty work before dropping local state.
- Do not auto-push, create issues, merge, delete branches, or drop stashes unless policy allows that specific side effect.
- Final completion claims require fresh `git status -sb`, `git stash list`, `git worktree list --porcelain`, active branch scan, and Owner governance evidence when applicable.
