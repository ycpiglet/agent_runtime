---
id: TASK-AR-529
display_id: TASK-AR-529
task_uid: 93277502-ad30-4b2a-a897-2213fe38ffbf
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 4500
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - footprint
  - gate
  - wave-safety
  - candidate
---

# TASK-AR-529 - Post-hoc actual-vs-declared footprint verification gate

## Goal

- Close the parallel-wave conflict-safety weak link: `footprint_conflict_gate --check` only compares *declared* `target_files`, so a unit that omits a file it actually touches can be dispatched in parallel and collide on the undeclared file with no gate catching it. Add a *post-hoc* check that compares actual vs declared footprint. (GH #125)

## Scope

- After a unit completes, derive actual changed files (`git diff --name-only`) and compare to declared `target_files`: `actual ⊄ declared` -> fail/warn, and feed the delta back to improve next declarations.
- Move undeclared-footprint wave participation from soft `watch` to `block` (a unit with no declaration cannot enter a parallel wave).
- Document the worktree backstop in wave-conductor docs: claim+worktree isolation degrades an undeclared collision from live corruption to a merge conflict; enforce actual-footprint comparison at the merge step as a second net.

## Acceptance Criteria — candidate

- Adoption (accept/defer/reject) is decided by the TASK-AR-527 deliberation; this file pre-registers the concrete, low-difficulty proposal so it is tracked rather than lost.

## Acceptance Criteria

- A gate (new, or integrated into `taskset_boundary_gate` / merge queue) flags `actual ⊄ declared` after unit completion.
- Undeclared footprint blocks parallel-wave participation instead of only warning.
- Wave-conductor docs state the worktree collision-degradation backstop.

## Evidence Targets

- `scripts/footprint_conflict_gate.py` (or merge-queue integration) + tests.
- Wave-conductor documentation update.
- Source: GH ycpiglet/agent_runtime#125.
