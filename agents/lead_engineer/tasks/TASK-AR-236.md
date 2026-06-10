---
completed_at: 2026-06-10T22:56:04+09:00
id: TASK-AR-236
status: completed
verification_status: passed
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
## RSI Planning Loop Implementation Slice (2026-06-10)

- Implementation evidence: `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md`.
- Runtime path: `scripts/planning_loop.py`.
- Verification wrapper prepared but not run in this slice: `scripts/verify_rsi_planning_taskset.py`.
- Current boundary: implementation is patched and proposal artifacts exist, but task-set completion is pending explicit verification execution.

## RSI Planning Taskset Closeout (2026-06-10T22:53:49+09:00)

- Verification report: `reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Completion boundary: local RSI planning loop implementation, proposal-only B-mode, UI Planner visibility, guardrails, and C-mode blocking.
- External release, remote publication, dependency install, secret/prod-data, destructive changes, and owner-only decisions remain out of scope.
