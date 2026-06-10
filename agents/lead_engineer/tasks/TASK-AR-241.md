---
id: TASK-AR-241
status: planned
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 12
est_tokens: 2200
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - retro
  - compound
  - history
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - agents/lead_engineer/compound_log.md
  - reviews/MEETING-2026-06-10-agent-runtime-rsi-planning-loop.md
created: 2026-06-10
---

## Goal

Build a review/compound/retro synthesizer that reads historical tasks, reviews, compounds, release records, and repeated corrections to propose future prevention work.

## Scope

- Detect recurring failures and near-misses across reviews, compounds, task logs, and status updates.
- Produce retro summaries with likely future failure modes.
- Create proposal records for preventive tasks, gate updates, eval expansion, or doc repairs.
- Preserve minority reviewer concerns and unresolved assumptions.

## Completion Criteria

- The synthesizer produces a structured retro report from existing history.
- Repeated patterns create deduped proposals with evidence chains.
- Proposed work distinguishes immediate fix, systemic prevention, and watch-only observation.
- Tests cover repeated correction, single weak signal, and resolved pattern cases.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-241 planned
- review: draft
- gate: pending
