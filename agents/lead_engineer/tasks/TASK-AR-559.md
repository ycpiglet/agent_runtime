---
id: TASK-AR-559
display_id: TASK-AR-559
task_uid: f6f4ad66-c4ab-488e-b41e-e01f1a57dba0
registered_at: 2026-06-15T00:29:41+09:00
created_at: 2026-06-15T00:29:41+09:00
updated_at: 2026-06-15T00:29:41+09:00
status: planned
priority: P1
difficulty: L
est_hours: 8
est_tokens: 7000
owner: lead_engineer
task_set_id: TASKSET-AR-AGENT-ORG-DELEGATION
tags:
  - agent-org
  - delegation
---

# TASK-AR-559 - Seam + risk dispatch gate

## Goal

- scripts/dispatch_gate.py: footprint-disjoint seam check (reuse footprint_conflict_gate) + risk-based auto-vs-Owner-gate decision (risk_tier/approval_required/budget_cap/escalation_triggers), auditable per Unit.

## Refs

- Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md
- Research: reviews/RESEARCH-2026-06-14-agent-org-design-references.md
