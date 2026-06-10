# Parallel Agent Worktree Protocol

## Purpose

Allow multiple Codex and Claude sessions to make progress in parallel without
mixing file edits, git index state, or handoff records.

## Rules

1. The main checkout is the orchestrator workspace. It assigns tasks, reviews
   branches, runs final gates, merges, and updates shared SSoT files.
2. Worker agents use one git worktree and one branch per task.
3. One active task can have exactly one active claim.
4. A role can have multiple active instances when each instance has unique
   `agent_instance_id` and `callsite_id`.
5. Active claims require `handoff_path` and `log_path` so a later session can
   resume from repo state without chat history.
6. Shared SSoT files are not directly edited by workers unless the task packet
   names them as owned files. Workers should write proposals or task-local docs.

## Claim Record

Claim files live under `agents/runtime/task_claims/*.json`.

```json
{
  "schema": "agent-runtime-task-claim/v1",
  "claim_id": "CLAIM-YYYYMMDD-HHMMSS-task-example",
  "task_id": "TASK-EXAMPLE",
  "agent_role": "lead-engineer",
  "agent_instance_id": "lead-engineer-A",
  "callsite_id": "terminal-1",
  "status": "working",
  "worktree_path": ".worktrees/TASK-EXAMPLE",
  "branch": "codex/task-example-parallel-runtime",
  "claimed_at": "2026-06-10T12:00:00+09:00",
  "last_heartbeat": "2026-06-10T12:05:00+09:00",
  "handoff_path": "STATUS.md",
  "log_path": "reviews/REVIEW-YYYYMMDD-parallel-session-protocol.md"
}
```

## Gate

Run:

```bash
python scripts/parallel_worktree_gate.py --check
```

The gate fails for duplicate active task claims, worker claims in the main
checkout, duplicate agent instances across tasks, duplicate worktrees across
tasks, missing instance metadata, and missing handoff/log pointers.

## Dispatch Pattern

```bash
git worktree add .worktrees/TASK-EXAMPLE -b codex/task-example-parallel-runtime main
```

Then start the agent inside that worktree with a task packet that names the task
ID, allowed files, forbidden shared docs, verification commands, evidence
outputs, and claim metadata.

## Recovery Pattern

1. Read `STATUS.md` for the current handoff.
2. Read `agents/runtime/task_claims/*.json` for active claims.
3. Open the claim's `log_path` and `handoff_path`.
4. Continue in the claim's `worktree_path` and `branch`, or release the claim
   after writing an explicit handoff.
