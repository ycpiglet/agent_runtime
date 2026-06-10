---
completed_at: 2026-06-10T22:56:04+09:00
id: TASK-AR-238
display_id: TASK-AR-238
task_uid: e79087b1-0d5f-46c9-8c6c-4e07b7d09f75
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
status: completed
verification_status: passed
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
  - agents/project/PLANNING-LOOP-CONTRACT.md
  - schemas/planning-proposal.schema.json
  - agents/project/PLANNING-GUARDRAILS.yml
  - scripts/planning_loop.py
  - scripts/verify_rsi_planning_taskset.py
  - reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md
  - agents/planning/scans/SCAN-20260610-rsi-planning.json
  - scripts/close_rsi_planning_taskset.py
  - reviews/RSI-PLANNING-TASKSET-VERIFY.json
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
## RSI Planning Loop Implementation Slice (2026-06-10)

- Implementation evidence: `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md`.
- Runtime path: `scripts/planning_loop.py`.
- Verification wrapper prepared but not run in this slice: `scripts/verify_rsi_planning_taskset.py`.
- Current boundary: implementation is patched and proposal artifacts exist, but task-set completion is pending explicit verification execution.

## RSI Planning Taskset Closeout (2026-06-10T22:53:49+09:00)

- Verification report: `reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Completion boundary: local RSI planning loop implementation, proposal-only B-mode, UI Planner visibility, guardrails, and C-mode blocking.
- External release, remote publication, dependency install, secret/prod-data, destructive changes, and owner-only decisions remain out of scope.
