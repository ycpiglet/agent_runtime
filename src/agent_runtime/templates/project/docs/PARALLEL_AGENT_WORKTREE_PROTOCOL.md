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
5. `display_name` is a readable UI/status label only. It must not be used as
   the durable identity; use `agent_role`, `agent_instance_id`, `callsite_id`,
   `claim_id`, `task_id`, `worktree_path`, and `tags` for system behavior.
6. Active claims require `handoff_path` and `log_path` so a later session can
   resume from repo state without chat history.
7. Shared SSoT files are not directly edited by workers unless the task packet
   names them as owned files. Workers should write proposals or task-local docs.

## Claim Record

Claim files live under `agents/runtime/task_claims/*.json`.

```json
{
  "schema": "agent-runtime-task-claim/v1",
  "claim_id": "CLAIM-YYYYMMDD-HHMMSS-task-example",
  "task_id": "TASK-EXAMPLE",
  "agent_role": "lead-engineer",
  "agent_instance_id": "le-20260610-143012-kst-a7f3",
  "display_name": "lead_engineer@design-01",
  "callsite_id": "terminal:wt-task-example:tab-01",
  "mode": "design",
  "status": "working",
  "worktree_path": ".worktrees/TASK-EXAMPLE",
  "branch": "codex/task-example-design-01",
  "claimed_at": "2026-06-10T12:00:00+09:00",
  "last_heartbeat": "2026-06-10T12:05:00+09:00",
  "expires_at": "2026-06-10T12:30:00+09:00",
  "handoff_path": "agents/runtime/task_claims/CLAIM-YYYYMMDD-HHMMSS-task-example.handoff.md",
  "log_path": "agents/runtime/task_claims/CLAIM-YYYYMMDD-HHMMSS-task-example.log.md",
  "tags": ["planning", "no-ssot-write"]
}
```

## Gate

Run:

```bash
python scripts/parallel_worktree_gate.py --check
```

The gate fails for duplicate active task claims, worker claims in the main
checkout, duplicate agent instances across tasks, duplicate worktrees across
tasks, missing instance/display metadata, and missing handoff/log pointers.

## Dispatch Pattern

```bash
python scripts/task_claim_dispatcher.py create --task-id TASK-EXAMPLE --agent-role lead-engineer --mode design --tag planning --tag no-ssot-write
git worktree add .worktrees/TASK-EXAMPLE -b codex/task-example-design-01 main
```

Then start the agent inside that worktree with a task packet that names the task
ID, allowed files, forbidden shared docs, verification commands, evidence
outputs, and claim metadata.

Good display names should read like RPG party/status labels: short, scannable,
and distinct. Prefer labels such as `lead_engineer@meeting-01`,
`lead_engineer@design-01`, or `claude:release_steward:task-ar-240:qa`.

## Recovery Pattern

1. Read `STATUS.md` for the current handoff.
2. Read `agents/runtime/task_claims/*.json` for active claims.
3. Open the claim's `log_path` and `handoff_path`.
4. Continue in the claim's `worktree_path` and `branch`, or release the claim
   after writing an explicit handoff.
