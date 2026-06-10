---
id: TASK-AR-235
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
  - read-only
  - evidence
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - agents/lead_engineer/tasks/TASK-AR-234.md
created: 2026-06-10
---

## Goal

Implement a read-only planning scan that compares backlog, status, roadmap, task files, reviews, eval artifacts, trace artifacts, release docs, and state machines.

## Scope

- Add a command or script that emits planning scan JSON.
- Detect stale plans, missing audit links, unresolved hold routes, repeated failures, eval regressions, release/version mismatch, and orphaned reviews.
- Report evidence and confidence; do not write canonical files.
- Reuse existing parsers and gates where possible.

## Completion Criteria

- Scan output is deterministic for the same repo state.
- Every finding includes source path, category, confidence, and suggested next action.
- Empty or weak evidence does not create a false positive task proposal.
- Tests cover missing sources, stale docs, and release/version mismatch examples.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-235 planned
- gate: pending
- document: draft
