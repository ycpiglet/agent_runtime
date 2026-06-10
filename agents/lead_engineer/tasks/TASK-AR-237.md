---
id: TASK-AR-237
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
tags:
  - rsi
  - planning-loop
  - hook-enforcement
  - schedule
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - docs/superpowers/plans/2026-06-10-rsi-planning-loop.md
  - agents/lead_engineer/tasks/TASK-AR-236.md
created: 2026-06-10
---

## Goal

Connect the planning loop to safe triggers: cycle completion, task completion, scheduled scans, Stop hook checks, and UI command submission.

## Scope

- Add planning gate rules for when scan/proposal may run.
- Add hook/schedule integration in proposal-only mode.
- Add safety routing for high-risk boundaries.
- Ensure Stop hook output cannot create unreviewed canonical mutations.

## Completion Criteria

- Planning triggers can run repeatedly without producing unbounded proposals.
- Hook and schedule paths respect kill switch, budget, and owner boundary rules.
- UI command submission can request a scan but cannot bypass planning gates.
- Tests cover hook-triggered scan, schedule-triggered scan, and blocked mutation attempts.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-237 planned
- gate: pending
- hook_enforcement: configured
