---
id: TASK-AR-238
status: planned
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 14
est_tokens: 2400
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - planning-loop
  - ui-console
  - proposal-review
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - docs/UI_RUNTIME_COMMANDS.md
  - agents/lead_engineer/tasks/TASK-AR-237.md
created: 2026-06-10
---

## Goal

Add a UI Planner panel that shows planning scans, proposals, evidence, risk tier, reviewer opinions, and apply readiness.

## Scope

- Read planning scan JSON and proposal outbox records.
- Show proposal lifecycle: detected, proposed, under review, approved, rejected, applied, superseded.
- Support filtering by task, release, evidence type, risk tier, and department.
- Keep apply controls disabled until `TASK-AR-239` exists.

## Completion Criteria

- Operators can inspect why a proposal exists and which evidence supports it.
- The UI shows disagreement and reviewer verdicts without hiding minority concerns.
- The panel does not mutate canonical files before approved apply support.
- Tests cover planner panel rendering and missing-data states.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-238 planned
- gate: pending
- document: draft
