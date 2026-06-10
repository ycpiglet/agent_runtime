---
id: TASK-AR-239
status: planned
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 16
est_tokens: 2800
tags:
  - rsi
  - planning-loop
  - approved-apply
  - verification
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - agents/lead_engineer/tasks/TASK-AR-236.md
  - agents/lead_engineer/tasks/TASK-AR-238.md
created: 2026-06-10
---

## Goal

Implement approved proposal apply and verification so accepted planning proposals can update canonical docs safely.

## Scope

- Apply approved proposals to task files, backlog, status, roadmap, and related docs.
- Require verifier list and rollback path before apply.
- Regenerate generated views after changes.
- Block high-risk proposal apply without explicit owner approval.

## Completion Criteria

- Approved low-risk planning proposals can be applied reproducibly.
- Apply produces an audit record linking proposal, source evidence, changed files, and verification output.
- Failed verification leaves canonical docs either unchanged or clearly reverted.
- Owner governance, state-machine, backlog board, and diff checks pass after apply.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-239 planned
- gate: pending
- document: draft
