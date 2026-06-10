# Parallel Agents And Worktrees Research

## Bottom Line

Parallel agent work is feasible when the repository separates execution state
by task. The safe pattern is not "three terminals in one checkout"; it is
orchestrator checkout plus per-task worktrees, branches, task claims, session
identity, and explicit handoff/log pointers.

## Source Map

| Source | Relevant point | Project implication |
| --- | --- | --- |
| Git worktree docs: https://git-scm.com/docs/git-worktree | A repository can have multiple working trees attached to it. | Use one worktree per task so file edits and checked-out branches do not share the main working tree. |
| Claude Code subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents | Subagents are specialized assistants with separate context and configurable tool permissions. | Role specialization is useful, but task ownership still needs repo-local claim metadata. |
| Claude Code git worktrees: https://docs.anthropic.com/en/docs/claude-code/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees | Claude documents parallel sessions with git worktrees. | Adopt worktree-per-task as the default for Claude workers. |
| OpenAI Codex subagents: https://developers.openai.com/codex/concepts/subagents | Codex supports built-in subagents and task-tool delegation. | Codex can delegate analysis/execution, but repo state must still be guarded by worktree and claim rules. |
| Running Codex safely: https://openai.com/index/running-codex-safely/ | Codex safety relies on sandboxing, approvals, network boundaries, and telemetry. | Keep low-risk local work smooth while gating release, destructive, external, and owner-only operations. |
| A2A task lifecycle: https://a2a-protocol.org/latest/topics/life-of-a-task/ | Agent work benefits from stable task identity and state transitions. | Use `task_id`, claim ID, and handoff/log paths as continuation keys. |
| AgentFarm multi-agent worktree paper: https://arxiv.org/abs/2604.14228 | Describes a multi-agent orchestration environment using Claude Code, Git worktrees, and append-only logs. | Similar independent research supports the same worktree + log + orchestrator design. |

## Interpretation

- Worktree isolation solves git index and file checkout collision, but not task
  ownership by itself.
- Task claims solve ownership, but not review safety by themselves.
- Handoff/log pointers solve session interruption, but not merge conflicts by
  themselves.
- The runtime needs all three: worktree, claim, and handoff.

## Recommended Protocol

1. Main checkout stays as orchestrator.
2. Each worker gets `.worktrees/<task-id>` and a task branch.
3. Each active worker writes `agents/runtime/task_claims/<claim-id>.json`.
4. Shared SSoT files are orchestrator-owned by default.
5. Worker outputs go to task-local docs, reviews, tests, and proposals.
6. Merge is sequential through orchestrator; workers rebase after each merge.

## Tooling Implication

- `parallel_worktree_gate.py` validates the claim protocol now.
- `TASK-AR-246` should add dispatcher helpers to create/release claims and spawn
  worktrees.
- `TASK-AR-236` proposal outbox can double as a claim/request queue for future
  planning loops, but it should not replace task claims.
