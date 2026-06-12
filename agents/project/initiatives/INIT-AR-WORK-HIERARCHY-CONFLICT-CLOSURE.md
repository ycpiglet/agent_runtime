---
type: initiative
id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
status: planned
owner: lead_engineer
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-12T08:17:54+09:00
priority: High
task_sets:
  - TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
---

# Work Hierarchy Conflict Closure Initiative

## Purpose

Remove the remaining collaboration conflict surfaces in work registration:
ambiguous `project` vocabulary, task display ID collisions, shared manual
`BACKLOG.md` edits, and worker dispatch before task detail is unit-ready.

## Decision

- Use `initiative -> taskset -> task -> unit` for Owner-facing decomposition.
- Reserve `project` for host/repository/product identity, such as
  `agent_runtime` or a downstream host project.
- Use `taskset` when the Owner wants a batch of tasks registered.
- Use `unit` only when a task already exists and needs worker-ready execution
  packets.

## Scope

- Update PM language contracts and generated host-project guidance.
- Add collision-resistant registration workflow tasks.
- Keep the active next-session pointer unchanged; this initiative is planned
  work, not an immediate claim.

## Out Of Scope

- Reopening completed PM, RSI, Vision, or Ops tasksets.
- Renumbering existing task files.
- Changing remote GitHub, CI, or deployment state.

## Success Signal

- A future agent can register new work without editing shared backlog sections
  by hand or racing another pane for task display IDs.
- The Owner can ask for `initiative`, `taskset`, `task`, or `unit` and get a
  predictable record shape.

