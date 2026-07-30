---
name: merge-integrator
version: 1.2.0
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
host-required gates -> merge (local) or print PR commands (--pr-mode) -> next
-> regenerate the board once per batch`. Mutating commands enforce a
repository-common cross-process lock and atomically replace one queue state
file in the primary checkout, so invocations from linked worktrees cannot
split or silently overwrite state.

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
`--verify` (repeatable) to replace that narrow default. It never replaces
host-required gates. A branch already queued in an active or `pr-handoff`
status must be `remove`d before re-enqueue.

`--depends-on-task` is repeatable and queue-local. Keep predecessor entries in
queue history until their dependents are processed. Before any git mutation,
the queue fails closed on an unknown predecessor, a failed/in-flight unmet
predecessor, or a cycle, and otherwise uses stable topological order rather
than FIFO. Dependency-bearing entries are local-mode only: `--pr-mode` refuses
them because printing a PR handoff cannot prove that the predecessor reached
the remote base.

## Host-required gates

An optional host-owned `agents/host/MERGE-GATES.json` makes product gates
mandatory:

```json
{
  "schema": "agent-runtime-merge-gates/v1",
  "protected_paths": [
    "agents/host/MERGE-GATES.json",
    "package.json",
    "playwright.config.ts",
    "scripts/merge_queue.py",
    "tests/visual/**"
  ],
  "gates": [
    {
      "id": "design-check",
      "command": "npm run design:check",
      "include_paths": ["src/**", "app/**", "components/**", "styles/**"]
    },
    {
      "id": "design-visual",
      "command": "npm run design:visual",
      "include_paths": ["src/**", "app/**", "components/**", "styles/**"]
    }
  ]
}
```

Absence (or an empty gate list) preserves legacy behavior. A nonempty gate
list requires nonempty `protected_paths`, including the policy file itself.
List every repository-controlled launcher, script, configuration, test,
baseline, and package manifest that could weaken a required gate. Enqueue
validates the policy and binds its canonical digest plus ordered gate IDs to
the entry. Process reloads policy from the integration base before mutation;
missing bindings or policy drift require removal and re-enqueue. Worker
changes matching `protected_paths` are rejected before any required gate runs.
Intentional gate-control changes therefore use a separate owner-controlled
policy lane, not an ordinary worker queue entry.

`include_paths` and `exclude_paths` select gates from the actual rebased diff.
Commands are argv-parsed without a shell. Only `{task_id}`, `{branch}`, and
`{base}` placeholders are supported. Required gates run after narrow
verification, cannot be removed by `--verify`, and fail before local merge or
PR handoff.

## Process (serial)

```powershell
# dry-run first: prints the plan, mutates nothing
python scripts/merge_queue.py process --dry-run

# local serial merge into the integration branch
python scripts/merge_queue.py process --all --base origin/main

# Dependency-free PR handoff: rebase + plain push + print gh commands
# (no remote merge here)
python scripts/merge_queue.py process --all --pr-mode
```

`--once` processes only the first pending entry. A failing entry is marked
`failed` with a `feedback-<branch>.md` file telling the worker how to rebase,
re-verify, and re-enqueue; the queue continues with eligible independent
entries and never poisons the integration branch. After a clean local batch,
the board is regenerated once (`python scripts/backlog_board.py --write`).

## Safety Boundaries (hard invariants)

- Every `enqueue`, `remove`, and non-dry-run `process` holds the same lock under
  `git rev-parse --git-common-dir`; contention times out with an actionable
  error (`MERGE_QUEUE_LOCK_TIMEOUT_SECONDS` controls the bounded wait).
- Every linked worktree resolves `queue.json` and feedback files to the primary
  checkout, so the common lock protects one physical state file rather than
  several per-worktree copies.
- `queue.json` is written to a same-directory temporary file, flushed, and
  atomically replaced. `list` and `process --dry-run` create no lock or state
  mutation and observe either the old or new complete JSON.
- Dependency validation and ordering finish before fetch, checkout, rebase, or
  merge. A predecessor that fails during the same batch leaves its dependents
  pending while later independent entries remain eligible.
- Host gate policy is read from the integration base, never the worker branch.
  Enqueue-bound policy drift, unbound legacy entries under a nonempty policy,
  protected gate-control edits, launch errors, and required-gate failures all
  fail closed before merge.
- NEVER force-pushes and NEVER deletes branches.
- Failed rebases/merges are aborted and the work tree is restored.
- `--pr-mode` performs no remote merge: it pushes the rebased branch only when
  the push is a plain fast-forward/new ref, then PRINTS the `gh pr create` /
  `gh pr merge` / `merge_queue.py remove` commands for the orchestrator.
- `--pr-mode` fails closed if a selected entry declares dependencies;
  `pr-handoff` is never treated as proof that a predecessor merged.
- Preflight refuses to run with a dirty integrator checkout or detached HEAD.
- Remote pushes and `gh` mutations are Owner/orchestrator actions: the queue
  prints them, the Owner runs them.

## W0->W6 Touchpoints

- W4: each entry's narrow verification and applicable host-required gates are
  the integration-time checks (worker W4a/W4b already happened upstream).
- W5: serial join into main is the wave's integration step; the wave hint
  prints board-regen, evidence-index, and the retro follow-ups.
- W6: `remove` the branch after its PR merges (in `--pr-mode`).
