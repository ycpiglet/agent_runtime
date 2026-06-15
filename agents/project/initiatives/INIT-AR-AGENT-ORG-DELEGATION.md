---
title: Agent Org & Delegation Model
status: active
owner: managing_partner
task_set_id: TASKSET-AR-AGENT-ORG-DELEGATION
created_at: 2026-06-15T00:29:41+09:00
updated_at: 2026-06-15T00:29:41+09:00
---

# INIT-AR-AGENT-ORG-DELEGATION — Agent Org & Delegation Model

Operationalize a Director→Lead→Worker+Reviewer agent org by reconciling the
template org-suite (roles.yml / orchestrator / subagent perspectives / seminar)
with the repo's claim/wave execution and the work-schema unit flow.

- Spec: `docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md`
- Research: `reviews/RESEARCH-2026-06-14-agent-org-design-references.md`
- Posture: seam-aware parallelism + phased autonomy; risk-based hybrid dispatch;
  swappable WorkerBackend (sub-agents now → headless daemon later); persona
  diversity as a blind-Delphi deliberation layer; token cost binding (~15x).

Units: TASK-AR-557 (role registry) · 558 (lead decomposition) · 559 (seam+risk
dispatch gate) · 560 (orchestrator + WorkerBackend) · 561 (persona deliberation
layer) · 562 (org/state read-API).
