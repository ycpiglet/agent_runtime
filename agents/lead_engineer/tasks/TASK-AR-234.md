---
id: TASK-AR-234
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1800
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - planning-loop
  - state-machine
  - governance
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/MEETING-2026-06-10-agent-runtime-rsi-planning-loop.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - docs/superpowers/plans/2026-06-10-rsi-planning-loop.md
created: 2026-06-10
---

## Goal

Define the planning loop contract and state machine for bounded recursive self-improvement, starting with proposal-only B-mode.

## Scope

- Define `planning_loop` lifecycle states and transitions.
- Define proposal schema fields: source refs, trace id, dedupe key, risk tier, action type, target files, rollback path, verifier list, and owner boundary.
- Define B-mode and C-mode boundaries.
- Document non-goals: no release/version/external/destructive/prod-data mutation without explicit approval.

## Completion Criteria

- `agents/project/STATE-MACHINES.yml` includes planning loop states.
- A proposal schema or contract document exists and is linked from the backlog.
- The contract explains when a scan may create proposals and when it must stay silent.
- Owner governance and state-machine gates pass.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-234 planned
- gate: pending
- document: draft
