---
name: merge-integrator
version: 1.1.0
description: Use when the user asks to integrate parallel worker branches, run the merge queue, serially rebase-test-merge branches into main, or hand off branches as PRs after a wave completes.
triggers:
  - merge queue
  - integrate
  - 머지큐
dependencies:
  - scripts/merge_queue.py
  - scripts/owner_governance_gate.py
  - scripts/backlog_board.py
registry_id: merge-integrator
template_path: src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
---

# Merge Integrator

Single-integrator serial queue that joins parallel worker branches into the
integration base one at a time: `fetch -> rebase -> narrow verification ->
merge (local) or print PR commands (--pr-mode) -> next -> regenerate the board
once per batch`. Mutating commands enforce a repository-common cross-process
lock and atomically replace queue state, so invocations from linked worktrees
cannot silently overwrite one another.

## When To Use

- A parallel wave finished and N worker branches are waiting to join main.
- Owner asks to "integrate", "run the merge queue", or "머지큐 돌려".

## Enqueue

```powershell
python scripts/merge_queue.py enqueue --branch <branch> --task-id TASK-AR-NNN `
    [--claim-id <id>] [--depends-on-task TASK-AR-NNN]... [--verify "<cmd>"]...
python scripts/merge_queue.py list
```

Default narrow verification is `python scripts/owner_governance_gate.py`; add
`--verify` (repeatable) to override. A branch already queued in an active or
`pr-handoff` status must be `remove`d before re-enqueue.

`--depends-on-task` is repeatable and queue-local. Keep predecessor entries in
queue history until their dependents are processed. Before any git mutation,
the queue fails closed on an unknown predecessor, a failed/in-flight unmet
predecessor, or a cycle, and otherwise uses stable topological order rather
than FIFO. In PR mode, `pr-handoff` satisfies queue ordering only; the
orchestrator still confirms the remote merge before removing history.

## Process (serial)

```powershell
# dry-run first: prints the plan, mutates nothing
python scripts/merge_queue.py process --dry-run

# local serial merge into the integration branch
python scripts/merge_queue.py process --all --base origin/main

# PR handoff: rebase + plain push + print gh commands (no remote merge here)
python scripts/merge_queue.py process --all --pr-mode
```

`--once` processes only the first pending entry. A failing entry is marked
`failed` with a `feedback-<branch>.md` file telling the worker how to rebase,
re-verify, and re-enqueue; the queue continues and never poisons the
integration branch. After a clean local batch, the board is regenerated once
(`python scripts/backlog_board.py --write`).

## Safety Boundaries (hard invariants)

- Every `enqueue`, `remove`, and non-dry-run `process` holds the same lock under
  `git rev-parse --git-common-dir`; contention times out with an actionable
  error (`MERGE_QUEUE_LOCK_TIMEOUT_SECONDS` controls the bounded wait).
- `queue.json` is written to a same-directory temporary file, flushed, and
  atomically replaced. `list` and `process --dry-run` create no lock or state
  mutation and observe either the old or new complete JSON.
- Dependency validation and ordering finish before fetch, checkout, rebase, or
  merge. A predecessor that fails during the same batch leaves its dependents
  pending and stops further dependent integration.
- NEVER force-pushes and NEVER deletes branches.
- Failed rebases/merges are aborted and the work tree is restored.
- `--pr-mode` performs no remote merge: it pushes the rebased branch only when
  the push is a plain fast-forward/new ref, then PRINTS the `gh pr create` /
  `gh pr merge` / `merge_queue.py remove` commands for the orchestrator.
- Preflight refuses to run with a dirty integrator checkout or detached HEAD.
- Remote pushes and `gh` mutations are Owner/orchestrator actions: the queue
  prints them, the Owner runs them.

## W0->W6 Touchpoints

- W4: each entry's narrow verification is the integration-time gate (worker
  W4a/W4b already happened upstream).
- W5: serial join into main is the wave's integration step; the wave hint
  prints board-regen, evidence-index, and the retro follow-ups.
- W6: `remove` the branch after its PR merges (in `--pr-mode`).
