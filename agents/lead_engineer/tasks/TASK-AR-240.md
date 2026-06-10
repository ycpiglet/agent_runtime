---
id: TASK-AR-240
status: planned
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
tags:
  - release-gate
  - version-consistency
  - rsi
  - stewardship
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - STATUS.md
  - BACKLOG.md
  - agents/project/ROADMAP.md
created: 2026-06-10
---

## Goal

Create a version and release consistency steward that checks release state, version strings, decision windows, tags, release docs, and task/review evidence alignment.

## Scope

- Compare `pyproject.toml`, package version, release docs, release-state records, tag plans, `STATUS.md`, `BACKLOG.md`, `ROADMAP.md`, and release reviews.
- Detect stale decision dates, contradictory release state, missing owner approval, and unlinked release evidence.
- Produce proposal-only findings for planning loop consumption.
- Block C-mode promotion if release/version consistency has unresolved findings.

## Completion Criteria

- A release/version consistency report exists with pass/watch/block status.
- Findings include concrete source paths and recommended routing.
- The steward does not bump versions, create tags, push, or publish.
- Tests cover matching and mismatching release/version states.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-240 planned
- release: hold_for_data
- gate: pending
