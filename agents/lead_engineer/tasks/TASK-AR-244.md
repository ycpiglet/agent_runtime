---
id: TASK-AR-244
status: planned
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 16
est_tokens: 2800
tags:
  - rsi
  - safety
  - drift-control
  - budget
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - agents/project/STATE-MACHINES.yml
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
