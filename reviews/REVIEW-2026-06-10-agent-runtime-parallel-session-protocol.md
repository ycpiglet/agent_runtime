---
type: review
id: REVIEW-2026-06-10-agent-runtime-parallel-session-protocol
task: TASK-AR-246
audience: owner
status: pass
signal: pass
score: 92
priority: High
tags: [parallel-agents, worktree, task-claim, handoff, owner-brief]
---

# Parallel Session Protocol Review

## Bottom Line

- Summary: registered and partially enforced safe parallel agent work.
- Result: `TASK-AR-246`, protocol brief, research, state-machine domain, and executable claim gate are added.
- Boundary: dispatcher automation is planned next; current work validates the protocol and blocks unsafe claim states.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Duplicate task claim blocked | pass | `tests/test_parallel_worktree_gate.py` |
| Same role multi-instance allowed | pass | `lead-engineer-A` and `lead-engineer-B` in separate task worktrees |
| Main checkout worker blocked | pass | `task-claim:main-checkout-worker` |
| Handoff/log pointers required | pass | active claim validation |
| Hook/gate path wired | pass | `owner_governance_gate.py` runs `parallel_worktree_gate.py --check` |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Create protocol brief | lead-engineer | codex | `AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL.md` |
| Done | Add research record | research-agent | codex | `reviews/RESEARCH-2026-06-10-agent-runtime-parallel-agents-and-worktrees.md` |
| Done | Add executable gate | cicd-engineer | codex | `scripts/parallel_worktree_gate.py` |
| Done | Add task state machine | lead-engineer | codex | `task_claim` |
| Next | Add dispatcher helpers | lead-engineer | worktree-dispatcher | `TASK-AR-246` |

## Risks / Blockers

- Risk: stale task claim cleanup needs a release/expire path in `TASK-AR-246`.
- Risk: orchestrator merge sequencing still depends on operator discipline until dispatcher helpers exist.
- Blocker: none for registration and validation gate.

## Insight

- The user requirement maps cleanly to lease semantics: task occupancy is exclusive, agent role identity is not.
- The right instance name is role plus callsite metadata, such as `lead-engineer-A`, `lead-engineer-B`, or `lead-engineer@terminal-2`.
- Session continuation should be recoverable from repo files, not from memory or terminal scrollback.

## Decision

- Decision: prohibit same-folder worker parallelism.
- Decision: permit role-level parallelism only with distinct instance/callsite/worktree metadata.
- Decision: keep shared SSoT writes orchestrator-owned unless task ownership explicitly says otherwise.

## Next Steps

1. Implement claim create/release helpers under `TASK-AR-246`.
2. Add active task claims to UI state.
3. Use per-task worktrees for the first parallel batch: `TASK-AR-234`, `TASK-AR-240`, `TASK-AR-243`, and `TASK-AR-241`.
