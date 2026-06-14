# Host lock merge automation

`tests/fixtures/host/agent_runtime.lock.json` (and a host's own
`agent_runtime.lock.json`) is a **derived** artifact: it stores a digest over
every template file. So any two branches that touch templates regenerate it
with different digests and **collide on merge** — the thrash recorded in
`COMPOUND-2026-06-14-003` (PR #135 went `DIRTY` three times during the
knowledge-stack wave, each needing a manual re-merge + `lock --write`).

## How it works

Two committed pieces cooperate:

1. **Keep-ours merge driver** — `.gitattributes` routes the lock to a
   `merge=arlock-keepours` driver configured as `true`, which keeps "ours" and
   **suppresses the conflict**. It runs no script and spawns no subprocess, so it
   cannot deadlock (regenerating *inside* a merge driver does: git holds the
   merge, and rebuilding the lock needs the fully-merged template tree, which
   mid-merge is only reachable by spawning git — which then blocks on the merge.
   Confirmed on Windows.).
2. **`.githooks/post-merge`** — after the merge completes (working tree fully
   materialised) it runs `lock_merge_driver.py post-merge`, which regenerates
   every tracked `agent_runtime.lock.json` and **stages** the ones that changed.

Net: `git merge origin/main` completes with no conflict markers, and leaves the
correct, staged lock to fold into the merge commit (`git commit --amend --no-edit`,
or just commit it). No manual `lock --write`, no hand-resolved markers.

## Setup (one time, per clone/worktree)

```bash
python scripts/lock_merge_driver.py --install
```

This sets `merge.arlock-keepours.driver=true` and `core.hooksPath=.githooks`
(git does not allow committing either, for security). `core.hooksPath` also
activates the committed `pre-commit` hook. Verify:

```bash
git check-attr merge tests/fixtures/host/agent_runtime.lock.json
# tests/fixtures/host/agent_runtime.lock.json: merge: arlock-keepours
git config --get core.hooksPath          # .githooks
```

## Scope / boundary

- The driver + hook run only for **local** `git merge`. GitHub's server-side
  merge uses neither, so a PR can still show `DIRTY` against an advanced base —
  but once you `git merge origin/main` locally it resolves cleanly and the lock
  is regenerated + staged for you.
- The regenerated lock is byte-identical to `agent_runtime lock --write`, so
  `host-lock --check` / `release-preflight` stay green.
- If a merge has **other** conflicts it halts before `post-merge` runs; finish
  resolving, then `python scripts/lock_merge_driver.py post-merge` (or any
  `lock --write`) refreshes the lock.
- If neither piece is installed, merges fall back to a normal lock conflict;
  resolve with `agent_runtime lock --root tests/fixtures/host --write`.
