---
id: TASK-AR-521
display_id: TASK-AR-521
task_uid: ac308082-3864-48cc-912a-5fb5d163bba7
registered_at: 2026-06-13T02:54:38+09:00
created_at: 2026-06-13T02:54:38+09:00
updated_at: 2026-06-13T02:54:38+09:00
status: planned
priority: P2
difficulty: S
est_hours: 3
est_tokens: 3000
reservation_id: RES-20260613-025300-976a05e1-01
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - allocator-created
---

# Template governance chain parity sweep and parity test

## Goal
- Template owner_governance_gate.py is missing evidence_index_generator/context_knowledge_gate chain entries present in the root copy and the divergence grows with every new gate (W4b notes on TASK-AR-500/505/510). Sweep the template chain to parity where template-shipped scripts exist, document intentional gaps, and add a parity test so future gates cannot silently diverge.
