---
id: TASK-AR-246
status: in_progress
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
tags:
  - parallel-agents
  - worktree
  - task-claim
  - handoff
audit_log:
  - AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL.md
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-parallel-agents-and-worktrees.md
  - reviews/REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md
created: 2026-06-10
---

## Goal

Implement dispatcher helpers for safe parallel Codex/Claude work: one task per worktree, one active claim per task, and resumable handoff metadata for every active worker session.

## Scope

- Add commands or scripts to create and release `agents/runtime/task_claims/*.json`.
- Generate recommended worktree path, branch name, `agent_instance_id`, human-readable `display_name`, and `callsite_id`.
- Produce a task packet that includes allowed files, forbidden shared SSoT files, verification commands, evidence outputs, and handoff path.
- Show active claims in UI/runtime state so `lead_engineer@design-01`, `lead_engineer@meeting-01`, and other role instances are distinguishable.
- Keep orchestrator-only shared files protected unless a task explicitly owns them.

## Completion Criteria

- Claim creation refuses a task already actively claimed.
- Active claims require a readable `display_name`, while system identity remains `agent_role + agent_instance_id + callsite_id + claim_id + task_id + worktree_path + tags`.
- Worker claims pointing at the main checkout are blocked.
- Same role with different instance IDs can run in separate worktrees.
- Claim release writes or verifies handoff/log pointers before marking released.
- `parallel_worktree_gate.py`, owner governance gate, template smoke, and full tests pass.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-246 in_progress
- task_claim: claimed
- gate: pass
- document: formatted
