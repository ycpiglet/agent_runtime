---
name: wave-conductor
version: 1.0.0
description: Use when the user asks to plan or dispatch parallel work waves, run multiple panes in parallel, cascade vs parallel dispatch, or batch claim+worktree creation across a footprint-disjoint dependency DAG.
triggers:
  - wave
  - 병렬
  - parallel
  - dispatch
dependencies:
  - scripts/wave_dispatcher.py
  - scripts/footprint_conflict_gate.py
  - scripts/task_claim_dispatcher.py
registry_id: wave-conductor
template_path: src/agent_runtime/templates/project/skills/wave-conductor/SKILL.md
---

# Wave Conductor

Decompose a unit dependency DAG into topological waves and batch-issue
claim+worktree for one wave at a time. Within a wave no unit depends on
another and all `target_files` footprints are pairwise disjoint (verified by
`footprint_conflict_gate.footprints_overlap`); overlapping units defer to a
later wave.

## When To Use

- Owner asks to "run a wave", "병렬로 진행", or dispatch N panes at once.
- A taskset has several units that can advance independently and you want
  them scheduled by `depends_on` + footprint, not by hand.

## Plan First (read-only, no side effects)

```powershell
python scripts/wave_dispatcher.py --taskset <taskset-alias> --plan
python scripts/wave_dispatcher.py --taskset <taskset-alias> --plan --json
```

Use `--unit <id-or-path>` (repeatable) instead of `--taskset` to plan an
explicit set. The table shows each wave's units, statuses, footprints,
`depends_on`, plus `deferral:` (footprint overlap pushed later) and
`external-dep:` (refs outside the selection; not used for ordering) lines.

## Dispatch One Wave

```powershell
# cascade (default): issue exactly the next single unit (sequential parity)
python scripts/wave_dispatcher.py --taskset <alias> --dispatch --mode cascade

# parallel: batch-issue up to N units of the current wave
python scripts/wave_dispatcher.py --taskset <alias> --dispatch --mode parallel --max-panes 2
```

Each issued unit gets a worktree `.worktrees/<task_id>` and a branch, and the
claim is created via `task_claim_dispatcher.py` (which logs the
`claim_created` pane event itself -- this script writes no pane events). One
task gets at most one claim per batch; units whose task already has an active
claim are skipped.

## Track Progress

```powershell
python scripts/wave_dispatcher.py --taskset <alias> --status
```

State is derived from task claims: `complete` / `current` / `queued` waves and
per-unit `done|active|pending`. At a wave boundary the tool prints the
full-cycle guidance (pytest, precommit, integrate released branches via the
merge queue, then re-plan and dispatch the next wave).

## Safety Boundaries

- A unit is only dispatched when its wave is `current` and the unit is
  `pending`; never advance to the next wave until the previous one is fully
  completed/released.
- Footprint disjointness is enforced at plan time; do not hand-override a
  deferral -- fix the overlapping `target_files` instead.
- Plan-time disjointness only checks DECLARED `target_files`, so a unit that
  under-declares can collide undetected. After a unit completes, run the post-hoc
  check `footprint_conflict_gate.py --postverify --task-id <T> [--base <merge-base>]`
  to compare ACTUAL changed files (merge-base diff) vs declared; `actual ⊄ declared`
  surfaces as a watch (add `--enforce-undeclared` to block). **Worktree backstop:**
  because each unit runs in an isolated `.worktrees/<task_id>`, an undeclared
  collision degrades to a *merge conflict* at integration, NOT live corruption --
  the merge step is the second net (TASK-AR-529, GH #125).
- `parallel` mode sets `--allow-parallel-task-set`; only use it when the units
  are genuinely independent.

## W0->W6 Touchpoints

- W0: `--plan` / `--status` are read-only visibility.
- W2/W3: `--dispatch` issues claim+worktree (the worker then implements).
- W4-W6: at each wave boundary run the full cycle (verify, integrate via
  merge-integrator, retro) before dispatching the next wave.
