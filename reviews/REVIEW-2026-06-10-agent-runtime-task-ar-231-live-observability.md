---
type: review
id: REVIEW-2026-06-10-agent-runtime-task-ar-231-live-observability
task: TASK-AR-231
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [ui-console, live-updates, event-filtering, evidence, replay]
---

# TASK-AR-231 Live Observability Review

## Bottom Line

- Summary: `TASK-AR-231` is complete for polling-based observability.
- Result: the UI can filter runtime events and inspect derived errors, evidence, and replay records.
- Boundary: streaming and runtime execution remain deferred; this task is read-only observability.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Event filtering | pass | `ui_state.filter_events` and `/api/events?...` |
| Error panel | pass | error-severity events derive `errors` records |
| Evidence panel | pass | event/message `evidence` fields derive proof links |
| Replay panel | pass | task/goal-context events and messages derive replay records |
| Freshness | pass | records retain source path, kind, last update, and freshness where available |
| Tests | pass | `test_ui_state.py` 6 passed; `test_ui_console.py` 10 passed |
| Route smoke | pass | filtered `/api/events` returned one event; state exposed errors/evidence/replay |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add event filtering | lead-engineer | codex | `src/agent_runtime/ui_state.py` |
| Done | Add derived observability resources | lead-engineer | codex | `errors`, `evidence`, `replay` |
| Done | Add Evidence UI tab | lead-engineer | codex | `src/agent_runtime/ui_console.py` |
| Next | Add graph/state-machine/roadmap views | lead-engineer | codex | `TASK-AR-232` |

## Risks / Blockers

- Risk: polling can still miss transient external state that is never written to runtime files.
- Risk: replay is derived from available records only; it does not reconstruct hidden terminal history.
- Blocker: none for polling-based UI observability.

## Insight

- The UI becomes useful for long runs once it can narrow the event stream and show evidence without a CLI prompt.
- Derived read-only resources are safer than inventing new mutable log stores in the UI layer.

## Decision

- Decision: keep polling as the transport for this cycle.
- Decision: defer SSE until the runtime has a stable executor/heartbeat contract.
- Decision: move next to `TASK-AR-232` for graph, state-machine, and roadmap views.

## Next Steps

1. Build read-only graph/state-machine/roadmap panels.
2. Keep derived view records linked back to source paths.
3. Avoid command execution claims from visual summaries.
