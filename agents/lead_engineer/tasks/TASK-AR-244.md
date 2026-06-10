---
completed_at: 2026-06-10T22:56:04+09:00
id: TASK-AR-244
display_id: TASK-AR-244
task_uid: 8fbd6e5d-d879-4447-bca5-7c5940383dea
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
updated_at: 2026-06-11T00:00:00+09:00
status: completed
verification_status: passed
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 16
est_tokens: 2800
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - safety
  - drift-control
  - budget
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - agents/project/STATE-MACHINES.yml
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

Add stability, budget, drift, and non-divergence guardrails for recursive planning loops.

## Scope

- Cap proposal count, scan frequency, token/time budget, and nested planning depth.
- Add drift detection for repeated churn, weak evidence, contradictory proposals, and self-weakening gate changes.
- Define stop conditions, circuit breakers, kill switch, and owner escalation.
- Require rollback paths and verifier lists before apply.

## Completion Criteria

- Guardrail policy is machine-readable enough for future planning gates.
- Proposal generation stops when budget, repetition, or contradiction thresholds are hit.
- Self-modifying gate changes are blocked unless owner-approved and reviewed.
- Tests cover budget cap, dedupe, weak evidence, contradiction, and kill switch.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-244 planned
- gate: pending
- rsi_improvement: observing
## RSI Planning Loop Implementation Slice (2026-06-10)

- Implementation evidence: `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md`.
- Runtime path: `scripts/planning_loop.py`.
- Verification wrapper prepared but not run in this slice: `scripts/verify_rsi_planning_taskset.py`.
- Current boundary: implementation is patched and proposal artifacts exist, but task-set completion is pending explicit verification execution.

## RSI Planning Taskset Closeout (2026-06-10T22:53:49+09:00)

- Verification report: `reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Completion boundary: local RSI planning loop implementation, proposal-only B-mode, UI Planner visibility, guardrails, and C-mode blocking.
- External release, remote publication, dependency install, secret/prod-data, destructive changes, and owner-only decisions remain out of scope.
