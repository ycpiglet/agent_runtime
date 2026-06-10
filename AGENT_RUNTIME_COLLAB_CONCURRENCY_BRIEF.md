---
type: brief
id: AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF
audience: owner
status: pass
signal: pass
score: 96
priority: High
tags: [parallel-agents, collaboration, concurrency, worktree, owner-brief]
---

# Agent Runtime Collaboration Concurrency Brief

## Bottom Line

- Summary: recorded the real-time collaboration research and implemented the first executable concurrency layer for pane work.
- Result: `TASKSET-AR-COLLAB-CONCURRENCY` contains `TASK-AR-251` through `TASK-AR-256`.
- Boundary: this is local repo/runtime coordination; it does not claim external provider-live collaboration or remote publication evidence.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Research mapping | pass | `reviews/RESEARCH-2026-06-10-realtime-collab-conflict-patterns.md` |
| Append-only pane event log | pass | `scripts/pane_event_log.py` |
| SSoT write control | pass | `scripts/collaboration_concurrency_gate.py` |
| Worktree-first taskset start | pass | `scripts/taskset_dispatcher.py` |
| UI state exposure | pass | `agent_runtime.ui_state` collaboration resource |
| Governance integration | pass | `scripts/owner_governance_gate.py` |

## Insight

- Google Docs-style OT solves concurrent text editing, but agent runtime conflicts are mostly task/worktree/SSoT ownership conflicts.
- Figma/Notion-style object boundaries fit task, claim, pane, and worktree records better than whole-document merge.
- SNS/event-stream patterns fit runtime auditability: workers append events, while canonical boards are regenerated.

## Decision

- Decision: root checkout remains the orchestrator and shared SSoT writer.
- Decision: worker panes use actual task worktrees before claims are created.
- Decision: pane state is recorded as append-only events; `BACKLOG.md`, `STATUS.md`, `BACKLOG-BOARD.md`, and pointer files remain derived or orchestrator-owned.

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Record collaboration-platform research | lead-engineer | codex | `TASK-AR-251` |
| Done | Add pane event log | agent-runtime-core | codex | `TASK-AR-252` |
| Done | Add SSoT concurrency gate | risk-controller | codex | `TASK-AR-253` |
| Done | Auto-create task worktrees before claim | worktree-dispatcher | codex | `TASK-AR-254` |
| Done | Wire conflict gate into owner governance | cicd-engineer | codex | `TASK-AR-255` |
| Done | Expose collaboration state to UI API | ui-runtime-operator | codex | `TASK-AR-256` |

## Risks / Blockers

- Risk: existing panes must call `scripts/pane_event_log.py record` before the UI can fully replay pane status.
- Risk: local governance completion does not prove external provider-live collaboration or remote publish success.
- Blocker: none for local repo/runtime scope.

## Next Steps

1. Keep `TASKSET-AR-COLLAB-CONCURRENCY` archived unless a new canonical task is added.
2. Use `scripts/pane_event_log.py record` for future pane lifecycle events.
3. Treat any non-orchestrator `ssot_write_attempted` event as a blocking finding.
