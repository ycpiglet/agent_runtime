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
6. Active claims must expose task-set progress fields: `task_set_id`,
   `phase`, `progress_pct`, `step_index`, `step_total`, `status_text`, and
   `updated_at`.
7. An orchestration overlay (`overlay: true`) is not a worker checkout. It may
   omit only `worktree_path` and `branch`; it must still carry canonical
   identity/progress fields, parent linkage, `allow_parallel_task_set: true`,
   handoff/log paths, and
   `persistence: {mode: working_tree, scm_commit_authorized: false}`.
8. Shared SSoT files are not directly edited by workers unless the task packet
   names them as owned files. Workers should write proposals or task-local docs.

## Claim Record

Claim files live under `agents/runtime/task_claims/*.json`.

```json
{
  "schema": "agent-runtime-task-claim/v1",
  "claim_id": "CLAIM-20260610-120000-task-ar-246",
  "task_id": "TASK-AR-246",
  "agent_role": "lead-engineer",
  "agent_instance_id": "lead-engineer-A",
  "callsite_id": "terminal-1",
  "pane_id": "terminal-1",
  "status": "working",
  "task_set_id": "TASKSET-AR-PANE-PROGRESS",
  "phase": "implementation",
  "progress_pct": 48,
  "step_index": 3,
  "step_total": 6,
  "status_text": "Rendering task-set progress cards",
  "worktree_path": ".worktrees/TASK-AR-246",
  "branch": "codex/task-ar-246-parallel-runtime",
  "claimed_at": "2026-06-10T12:00:00+09:00",
  "last_heartbeat": "2026-06-10T12:05:00+09:00",
  "updated_at": "2026-06-10T12:05:00+09:00",
  "handoff_path": "STATUS.md",
  "log_path": "reviews/REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md"
}
```

## Progress Contract

- `task_set_id` identifies the pane/workflow bundle, not only the individual
  task. UI and handoff views aggregate active work by this field.
- `step_index` and `step_total` describe the current resumable step inside the
  task-set lane. `step_index` must be between `1` and `step_total`.
- `progress_pct` is a rough display value from `0` to `100`; it is not a release
  gate by itself.
- `status_text` is the human-readable resume sentence. It should say what the
  worker is doing now and what remains blocked or pending.
- `updated_at` changes when progress fields change. `last_heartbeat` changes
  when the worker proves the claim is still alive.
- Completion-like phases such as `completed` require the final step; unfinished
  work must stay in a working/review/blocking phase.

## Gate

Run:

```bash
python scripts/parallel_worktree_gate.py --check
```

The gate fails for duplicate active task claims, worker claims in the main
checkout, duplicate agent instances across tasks, duplicate worktrees across
tasks, missing instance metadata, malformed overlay contracts, and missing
handoff/log pointers. An out-of-`HEAD` working-tree overlay remains visible as
a reset/clean risk watch.

## Dispatch Pattern

```bash
git worktree add .worktrees/TASK-AR-246 -b codex/task-ar-246-parallel-runtime main
```

Then start the agent inside that worktree with a task packet that names the task
ID, allowed files, forbidden shared docs, verification commands, evidence
outputs, and claim metadata.

Claim creation leaves Git `HEAD` unchanged by default. When a control-repository
workflow explicitly uses `--commit-claim-artifacts`, `claim_guard.py` creates a
private, short-lived transaction record and passes its marker only to the
`git commit` child. The pre-commit gate accepts only the exact authorized claim
JSON when repository, starting `HEAD`, live owner process, private record,
indexed blob, and working-tree blob all match. The record is removed when
`git commit` exits. A missing, ambient, stale, malformed, wrong-root,
wrong-path, unstaged, or mismatched marker never weakens the ordinary
`HEAD`-persistence block.

## Recovery Pattern

1. Read `STATUS.md` for the current handoff.
2. Read `agents/runtime/task_claims/*.json` for active claims and use
   `task_set_id`, `phase`, `step_index`, `step_total`, `progress_pct`, and
   `status_text` to pick the correct pane state.
3. Open the claim's `log_path` and `handoff_path`.
4. Continue in the claim's `worktree_path` and `branch`, or release the claim
   after writing an explicit handoff.
