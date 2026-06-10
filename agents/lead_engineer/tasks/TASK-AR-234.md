---
completed_at: 2026-06-10T22:56:04+09:00
id: TASK-AR-234
status: completed
verification_status: passed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1800
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - planning-loop
  - state-machine
  - governance
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/MEETING-2026-06-10-agent-runtime-rsi-planning-loop.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - docs/superpowers/plans/2026-06-10-rsi-planning-loop.md
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

Define the planning loop contract and state machine for bounded recursive self-improvement, starting with proposal-only B-mode.

## Scope

- Define `planning_loop` lifecycle states and transitions.
- Define proposal schema fields: source refs, trace id, dedupe key, risk tier, action type, target files, rollback path, verifier list, and owner boundary.
- Define B-mode and C-mode boundaries.
- Document non-goals: no release/version/external/destructive/prod-data mutation without explicit approval.

## Completion Criteria

- `agents/project/STATE-MACHINES.yml` includes planning loop states.
- A proposal schema or contract document exists and is linked from the backlog.
- The contract explains when a scan may create proposals and when it must stay silent.
- Owner governance and state-machine gates pass.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-234 planned
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
