---
id: TASK-AR-258
display_id: TASK-AR-258
task_uid: f3096efc-ab50-4258-9a10-cce4221b4881
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Collaboration waiver burn-down and root capability promotion
status: completed
priority: P0
importance: Critical
difficulty: M
est_hours: 4
est_tokens: 1600
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: agent-runtime-core
owner: lead-engineer
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [governance, waiver, runtime-capability, ralph, retro, scribe, doc-steward]
audit_log: [agents/project/COLLABORATION-GOVERNANCE.json, agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json]
---

## Goal

Reduce explicit collaboration waivers by promoting safe root runtime capabilities and recording real artifact evidence.

## Completion Criteria

- Root `scripts/agent_loop.py` or equivalent satisfies Ralph capability evidence.
- Root `scripts/agent_retro.py` or `scripts/promote_retro_forward.py` satisfies retro capability evidence.
- Root `scripts/scribe_due.py` satisfies scribe capability evidence.
- Root `scripts/doc_steward_due.py` satisfies doc-steward capability evidence.
- `reviews/RETRO-*` evidence exists.
- The collaboration waiver file only contains subjects that are still genuinely unresolved.
- `python scripts/collaboration_governance_gate.py --root . --check` passes.

## Execution Notes

- Do not fabricate role usage. Keep `role-usage:scribe` waived until there is real claim/log evidence.
- Promoting a script means root users and Owner gates can inspect or execute it without relying on template-only paths.

## Result

- Promoted root `scripts/agent_loop.py`, `scripts/agent_retro.py`, `scripts/promote_retro_forward.py`, `scripts/scribe_due.py`, and `scripts/doc_steward_due.py`.
- Added `reviews/RETRO-2026-06-10-agent-runtime-governance-ops.md`.
- Reduced collaboration waiver subjects to only `role-usage:scribe`.
- Verified `collaboration_governance_gate.py --check`: `block=0`, `watch=5`, `waived=1`.
