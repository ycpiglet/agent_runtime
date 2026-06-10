---
type: brief
id: AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [parallel-agents, worktree, task-claim, handoff, owner-brief]
---

# Agent Runtime Parallel Session Protocol

## Bottom Line

- Summary: parallel Codex/Claude work is allowed only through per-task worktrees, task claims, and resumable handoff pointers.
- Rule: one active task can have one active claim; one role can have many active instances only when each has a unique `agent_instance_id`, readable `display_name`, `callsite_id`, branch, and worktree.
- Gate: `scripts/parallel_worktree_gate.py --check` is now included in owner governance, Stop hook, CI, and template sync paths through `owner_governance_gate.py`.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Same-directory multi-terminal risk | block | worker claim pointing at `.` fails as `task-claim:main-checkout-worker` |
| Task single-occupancy | pass | duplicate active claim on one task fails as `task-claim:duplicate-active-task` |
| Role multi-instance | pass | same role can run as `lead_engineer@design-01`, `lead_engineer@meeting-01`, etc. |
| Resume continuity | pass | active claims require `handoff_path` and `log_path` |
| Claim helper | watch | `scripts/task_claim_dispatcher.py create/release` now defines the display-name contract; full worktree spawn remains next |
| Template propagation | pass | project template includes `parallel_worktree_gate.py` and governance gate wiring |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add parallel task-claim gate | agent-runtime-core | codex | `scripts/parallel_worktree_gate.py` |
| Done | Wire gate into owner governance | cicd-engineer | codex | `scripts/owner_governance_gate.py` |
| Done | Propagate to host template | agent-runtime-core | codex | `src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py` |
| Done | Add state machine domain | lead-engineer | codex | `task_claim` in `STATE-MACHINES.yml` |
| In Progress | Implement dispatcher helpers for claim creation/release | lead-engineer | worktree-dispatcher | `scripts/task_claim_dispatcher.py` |

## Risks / Blockers

- Risk: terminal-only parallelism in one checkout shares files and git index, so it remains blocked for worker tasks.
- Risk: stale active claim files can block new workers until released or marked stale with a handoff note.
- Blocker: automated git worktree spawn/release orchestration is still registered as `TASK-AR-246`; current implementation covers claim creation/release records, validation gate, and protocol.

## Insight

- The game-like logout/login requirement is a state requirement, not a chat-memory requirement.
- Display names are character labels for humans, not identities for policy. The system identity is `agent_role + agent_instance_id + callsite_id + claim_id + task_id + worktree_path + tags`.
- Durable continuation needs three pointers: the task claim, the worktree/branch, and the handoff/log documents.
- Claude Code-style subagents and Codex subagents are useful execution surfaces, but repository safety still depends on task isolation and a single canonical writer for shared SSoT files.

## Decision

- Decision: use the main checkout as orchestrator only; worker agents use `.worktrees/<task-id>` and task branches.
- Decision: shared SSoT files such as `BACKLOG.md`, `STATUS.md`, `owner-docs.yml`, and `STATE-MACHINES.yml` are merged by the orchestrator unless a task explicitly owns that doc.
- Decision: every active claim must identify `agent_role`, `agent_instance_id`, `display_name`, `callsite_id`, `task_id`, `worktree_path`, `branch`, `handoff_path`, `log_path`, and policy/filter `tags`.

## Next Steps

1. Extend `TASK-AR-246` dispatcher helpers from claim record creation/release to actual per-task worktree spawn/cleanup.
2. Extend UI runtime state to show active task claims as session cards.
3. Keep `parallel_worktree_gate.py` in the Stop hook path so interrupted work leaves inspectable continuation pointers.
