---
id: TASK-AR-236
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - planning-loop
  - proposal-outbox
  - task-generation
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/MEETING-2026-06-10-agent-runtime-rsi-planning-loop.md
  - agents/lead_engineer/tasks/TASK-AR-235.md
created: 2026-06-10
---

## Goal

Add a proposal outbox and draft task writer so planning findings become inspectable proposals before they become canonical work.

## Scope

- Store proposals in a repo-local outbox with stable IDs.
- Support proposal types: new task, plan update, doc repair, eval expansion, release/version consistency issue, retro/compound follow-up.
- Generate draft task markdown without immediately registering it in canonical task order.
- Include dedupe keys and proposal supersession rules.

## Completion Criteria

- Proposal records are auditable and reversible.
- Duplicate findings collapse into one proposal unless evidence materially changes.
- Draft task output includes completion criteria, source evidence, verifier list, and risk boundary.
- No canonical docs are modified unless an approved apply step is invoked later.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-236 planned
- gate: pending
- document: draft
