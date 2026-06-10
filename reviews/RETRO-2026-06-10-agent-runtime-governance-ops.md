---
type: retro
id: RETRO-2026-06-10-agent-runtime-governance-ops
audience: owner
status: watch
signal: watch
score: 80
priority: P0
tags: [retro, governance, lifecycle, usage-metrics]
recorded_at: 2026-06-10T23:35:00+09:00
---

# RETRO-2026-06-10 agent runtime governance ops

## Bottom Line

- Summary: collaboration governance must move from broad pass/fail to measurable usage, reuse, lifecycle, and deprecation signals.
- Status: active follow-up under `TASKSET-AR-GOVERNANCE-OPS`.
- Boundary: role usage must not be fabricated; missing role evidence remains waived or watched until real claim/log evidence exists.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Waiver model | watch | `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json` |
| Capability promotion | action | `TASK-AR-258` |
| Asset usage metrics | action | `TASK-AR-260` |
| Lifecycle cleanup | planned | `TASK-AR-259` |
| Sync enforcement | planned | `TASK-AR-261` |

## Insight

- A tool existing in a template is not the same as a root runtime capability.
- A hook being installed is not enough; it must have evidence that it is wired, referenced, reused, and periodically reviewed.
- Low-use skills, hooks, triggers, and gates need a lifecycle decision instead of permanent accumulation.

## Decision

- Decision: create an asset registry and usage gate for skills, hooks, triggers, gates, and scripts.
- Decision: keep usage gaps visible as `watch` until there is enough evidence to block or deprecate.
- Decision: keep `role-usage:scribe` waived until real scribe claim/log evidence exists.

## §5 Forward Actions

| 종류 | 제안 | Tier | 우선순위 | Owner 제안 | 근거 |
|------|------|------|----------|-----------|------|
| TASK 후보 | Promote root Ralph/retro/scribe/doc-steward capabilities and reduce waiver subjects | — | P0 | lead-engineer | TASK-AR-258 |
| TASK 후보 | Add runtime asset usage registry and gate for skills/hooks/triggers/gates/scripts | — | P0 | lead-engineer | TASK-AR-260 |
| TASK 후보 | Normalize lifecycle drift and active claim metadata | — | P0 | release-integrity | TASK-AR-259 |
| TASK 후보 | Add state sync gate so backlog/status/pointer cannot drift silently | — | P0 | lead-engineer | TASK-AR-261 |
| TASK 후보 | Split root pytest and template pytest verification tiers | — | P1 | qa | TASK-AR-262 |
