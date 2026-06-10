---
id: TASK-AR-245
status: planned
owner: lead-engineer
priority: P1
difficulty: L
est_hours: 16
est_tokens: 2800
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - c-mode
  - promotion-gate
  - governance
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-240.md
  - agents/lead_engineer/tasks/TASK-AR-243.md
  - agents/lead_engineer/tasks/TASK-AR-244.md
created: 2026-06-10
---

## Goal

Define the long-term C-mode promotion gate for bounded auto-planning and low-risk auto-apply.

## Scope

- Define promotion prerequisites: scan stability, proposal precision, trace/eval linkage, release/version consistency, guardrail pass, rollback proof, and owner policy.
- Define allowed C-mode actions: low-risk plan hygiene, stale link repair, generated view refresh, proposal dedupe, and watch-only reminders.
- Define prohibited C-mode actions: release/version bump, tag, push, external publication, dependency install, secret/prod-data change, destructive change, owner-only decision.
- Define demotion triggers when churn, failed verification, or risky proposals increase.

## Completion Criteria

- C-mode promotion checklist exists and is enforced by a gate.
- At least three proposal-only cycles pass before any C-mode action is allowed.
- C-mode auto-apply actions have tests, rollback, and audit records.
- Demotion to B-mode happens automatically on gate failure or owner rejection.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-245 planned
- rsi_improvement: proposed
- gate: pending
