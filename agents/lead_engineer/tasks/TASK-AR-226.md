---
id: TASK-AR-226
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 8
est_tokens: 1400
tags:
  - ui-console
  - data-map
  - runtime-state
  - mvp
audit_log:
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
  - BACKLOG.md
  - BACKLOG-BOARD.md
  - docs/UI_RUNTIME_DATA_MAP.md
created: 2026-06-10
---

## Goal

Map the current `agent_runtime` state sources before building a web UI, so the UI reads the runtime as the source of truth instead of inventing a parallel state model.

## Scope

- Discover where the runtime stores tasks, agents, messages, events, goals, logs, state-machine records, and evidence.
- Classify each source as read-only, safe write-through API, command-outbox write, or forbidden direct mutation.
- Define normalized UI view records for `Task`, `Agent`, `Message`, `Event`, and `Goal`.
- Capture ordering semantics for backlog/task selection so UI reorder behavior does not corrupt runtime scheduling.

## Deliverables

- `docs/UI_RUNTIME_DATA_MAP.md`
- A source table with path/API, owner, freshness rule, identifier rule, and mutation boundary.
- A thin contract for the follow-up adapter/API task.

## Completion Criteria

- Every MVP panel in `AGENT_RUNTIME_UI_CONSOLE_BRIEF.md` maps to at least one runtime source or an explicit gap.
- The document states which fields are canonical and which fields are derived for UI convenience.
- The document includes the initial safe-write strategy for task updates, messages, and runtime commands.
- No UI implementation starts before this map identifies the data sources and write boundaries.

## Implementation Notes

- Prefer the existing runtime files and scripts over a new database for the first pass.
- Treat command files or runtime APIs as the only safe mutation path.
- Do not make the browser write arbitrary runtime files directly.

## Verification

- Review the data map against the brief's MVP list: backlog, current tasks, kanban, agents, events, messages, goal status, and task detail.
- Run the existing owner/backlog format gate after registering this task in the board.

## State Machine Mapping

| Machine | Current State | Trigger | Evidence |
|---|---|---|---|
| `cycle` | `done` | `gates_pass` | `docs/UI_RUNTIME_DATA_MAP.md` covers the UI Console MVP source map. |
| `task` | `completed` | `done_criteria_met` | This task's deliverable is present and linked in `audit_log`. |
| `gate` | `pass` | `findings_zero` | Owner governance/backlog gates are expected after board regeneration. |
| `document` | `formatted` | `document_regenerated` | Data map is a stable follow-up contract for `TASK-AR-227`. |

## Completion Evidence

- 2026-06-10: Created `docs/UI_RUNTIME_DATA_MAP.md`.
- 2026-06-10: Mapped every MVP panel in `AGENT_RUNTIME_UI_CONSOLE_BRIEF.md` to runtime sources or explicit gaps.
- 2026-06-10: Defined canonical vs derived fields for `Task`, `Agent`, `Message`, `Event`, and `Goal`.
- 2026-06-10: Set initial safe-write strategy: API first, `.ui_outbox/COMMAND-*.json` fallback, no direct browser mutation of runtime files.
- 2026-06-10: Next implementation pointer is `TASK-AR-227` UI State API / File Adapter.
