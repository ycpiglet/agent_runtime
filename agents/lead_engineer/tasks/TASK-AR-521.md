---
id: TASK-AR-521
display_id: TASK-AR-521
task_uid: ac308082-3864-48cc-912a-5fb5d163bba7
registered_at: 2026-06-13T02:54:38+09:00
created_at: 2026-06-13T02:54:38+09:00
updated_at: 2026-06-13T13:20:00+09:00
started_at: 2026-06-13T09:47:58+09:00
completed_at: 2026-06-13T13:20:00+09:00
status: completed
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

## Completion Evidence

- PR #74: template owner_governance_gate chain parity (evidence_index_generator copied + wired, documented omissions) + ast-parsed parity test (7 tests).

## Verification Results

- pytest tests/test_owner_governance_chain_parity.py -q -> 7 passed
- owner_governance_gate (rebased worktree) -> exit 0
- W4b inst-w4b-ar521-verifier -> APPROVE
