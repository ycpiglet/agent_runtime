# Work Hierarchy Conflict Closure Plan

> **For agentic workers:** execute this taskset to remove the remaining shared
> work-registration conflict surfaces. Do not rename legacy task IDs or reopen
> completed tasksets unless a separate planner-approved record says so.

**Initiative:** `INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`

**Task Set:** `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`

**Goal:** Make work hierarchy language unambiguous and make task registration
collision-resistant enough for multiple panes/agents.

## Decision

Use `initiative -> taskset -> task -> unit`.

- `project`: host/repository/product identity, such as `agent_runtime`.
- `initiative`: taskset parent, outcome-level grouping.
- `taskset`: executable batch with one completion boundary.
- `task`: canonical accountable work item.
- `unit`: smallest worker-ready execution packet.

## Registered Tasks

| Task | Title | Intent |
| --- | --- | --- |
| `TASK-AR-369` | Initiative vocabulary and PM contract migration | Finish terminology migration across contracts, templates, docs, and board fields |
| `TASK-AR-370` | Task ID reservation ledger and create-task lock | Prevent display ID races before task files are created |
| `TASK-AR-371` | BACKLOG.md shared-write deconfliction | Move manual registration append traffic out of a shared conflict-prone surface |
| `TASK-AR-372` | Registration CLI/API for initiative/taskset/task/unit | Provide one command path for planners instead of hand-editing many files |
| `TASK-AR-373` | Unit-readiness migration report for legacy planned tasks | Identify planned tasks that still need worker-ready units before dispatch |
| `TASK-AR-374` | Conflict-surface verification and closeout gate | Prove the remaining conflict surfaces are closed and record handoff evidence |

## Phase 1: Vocabulary And Records

- [ ] Normalize docs to `initiative -> taskset -> task -> unit`.
- [ ] Keep `project_id` as legacy/host identity; add `initiative_id` to new task
  records.
- [ ] Add an initiative record and board metadata.

## Phase 2: Collision-Free Registration

- [ ] Add a task ID reservation ledger or allocator that atomically reserves
  display IDs before task files are written.
- [ ] Add a gate that fails duplicate display IDs, duplicate reservations, or
  stale abandoned reservations.
- [ ] Keep immutable `task_uid` as identity, but make human display IDs safe to
  allocate.

## Phase 3: Backlog Deconfliction

- [ ] Convert `BACKLOG.md` from a shared manual registration target into a
  generated/append-only changelog or index sourced from taskset registration
  records.
- [ ] Ensure `BACKLOG-BOARD.md` remains generated from task frontmatter.
- [ ] Preserve historical narrative entries without making every future planner
  touch the same top-of-file section.

## Phase 4: Registration API

- [ ] Add a planner-facing command that creates initiative, taskset, task, and
  optional unit records from one structured input.
- [ ] The command must update board metadata, task files, evidence pointers, and
  validation surfaces consistently.
- [ ] The command must refuse to run when another reservation/claim owns the
  requested display ID range.

## Phase 5: Migration And Closeout

- [ ] Report planned tasks that lack worker-ready units or equivalent detail.
- [ ] Add a closeout wrapper that runs identity, backlog, owner-doc, and taskset
  gates.
- [ ] Record a final review proving no shared registration file must be edited
  concurrently for normal work intake.

## Done Criteria

- Task registration no longer relies on manually choosing the next task number.
- `BACKLOG.md` no longer requires every planner to append a top section by hand.
- Worker dispatch can distinguish taskset planning from task execution and unit
  execution.
- The Owner-facing vocabulary is clear enough that short prompts route to the
  correct record layer.

