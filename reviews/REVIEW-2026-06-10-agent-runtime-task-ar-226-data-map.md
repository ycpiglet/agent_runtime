---
type: review
id: REVIEW-2026-06-10-agent-runtime-task-ar-226-data-map
audience: owner
status: pass
signal: pass
score: 95
priority: High
tags: [ui-console, data-map, runtime-state, handoff]
actions: [continue-task-ar-227]
owner: lead-engineer
due: 2026-06-10
evidence:
  - docs/UI_RUNTIME_DATA_MAP.md
  - agents/lead_engineer/tasks/TASK-AR-226.md
  - AGENT_RUNTIME_UI_CONSOLE_BRIEF.md
---

# TASK-AR-226 UI Runtime Data Map Review

## Bottom Line

- Summary: `TASK-AR-226` is complete; the UI Console now has a runtime data-source map before UI implementation starts.
- Output: `docs/UI_RUNTIME_DATA_MAP.md`.
- Next task: `TASK-AR-227` should implement the read-first state API / file adapter using this contract.

## Signal

| Item | State | Evidence |
|---|---|---|
| MVP panel mapping | pass | backlog, current tasks, Kanban, agents, events, messages, goal status, and task detail are mapped |
| Canonical vs derived fields | pass | `Task`, `Agent`, `Message`, `Event`, and `Goal` sections |
| Mutation boundary | pass | API first, `.ui_outbox/COMMAND-*.json` fallback |
| Runtime source split | pass | host-visible state and installed-template runtime state are separated |
| Remaining gap | watch | durable goal JSON SSoT does not exist yet; adapter must expose an explicit gap |

## Action Board

| Order | Task | Owner | Action |
|---:|---|---|---|
| 1 | `TASK-AR-227` | lead-engineer | Build read-first `/api/state` and normalized file adapter |
| 2 | `TASK-AR-228` | lead-engineer | Build read-only web console from adapter output |
| 3 | `TASK-AR-229` | lead-engineer | Add safe CRUD/reorder after canonical order strategy exists |

## Risks / Blockers

- Risk: current `BACKLOG-BOARD.md` order is generated, not canonical for drag-and-drop reorder.
- Risk: current root package repo has no live `agents/messages` or `agents/runtime/events` directories; adapter must tolerate missing runtime dirs.
- Blocker: none for `TASK-AR-227`; it can implement read endpoints with explicit gap records.

## Insight

- The UI should not parse CLI output. It should read task/frontmatter, board, session, message, event, and state-machine files directly.
- Goal status is the weakest current source because the active Codex goal is not fully persisted as a repo-local JSON record.
- Reorder support belongs in `TASK-AR-229`, not the read-only adapter, unless a canonical `order` field or runtime-owned order file is introduced.

## Decision

- Decision: treat `docs/UI_RUNTIME_DATA_MAP.md` as the contract for `TASK-AR-227`.
- Decision: keep the first UI backend read-only and side-effect-free.
- Decision: only allow UI writes through runtime API or `.ui_outbox`; direct browser file mutation is forbidden.

## Next Steps

| Step | Owner | Trigger |
|---|---|---|
| Start `TASK-AR-227` | lead-engineer | Data map committed |
| Add adapter tests first | lead-engineer | Before production adapter code |
| Preserve source freshness metadata | lead-engineer | Every API response |
