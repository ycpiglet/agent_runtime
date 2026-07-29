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
workflow explicitly uses `--commit-claim-artifacts`, `claim_guard.py` stages the
claim artifacts in the real index for visible recovery, then builds a mode
`0600` private index from the starting `HEAD`. Only the requested claim JSON,
handoff, and log enter that index; unrelated staged, partially staged,
unstaged, and untracked work stays outside the candidate tree.

The v2 transaction marker binds the repository, live owner process, symbolic
branch, starting `HEAD`, exact private-index path, sealed tree OID, and every
artifact path, mode, and blob OID. Repository `pre-commit`,
`prepare-commit-msg`, and `commit-msg` hooks run against the private index. The
gate accepts the temporary out-of-`HEAD` claim only when the private record,
marker, index, complete tree delta, indexed blobs, and working claim blob all
match.

After the hooks return, the guard rechecks the complete private tree, every
artifact's working blob, the private record, `HEAD`, and the symbolic branch.
It creates the commit from the already sealed tree with `git commit-tree`,
then enters a short publication critical section. The guard creates a private
mode-`0700` Git administrative context whose `HEAD` is detached at the
starting commit and whose `commondir` points to the repository's real common
Git directory. It exclusively acquires the actual worktree-specific
`HEAD.lock`, repeats the tree/blob/record/ref checks under that lock, and
advances the original branch with
`git update-ref <ref> <new> <old>` from the private context. The real
`HEAD.lock` prevents an equal-OID symbolic branch switch while Git's ref lock
and old-OID check still make a competing direct ref update win safely.

Repository-local `GIT_*` redirectors are removed before the transaction.
Hooks and `commit-tree` always use the real worktree context; the detached
private context is used only for the final ref compare-and-swap. Marker,
index, message, private-context, and owned lock files are removed on every
exit. A pre-existing `HEAD.lock` is never removed and makes the transaction
fail closed. Failure leaves the claim artifacts staged so the ordinary gate
blocks them. `post-commit` runs after publication and lock release; its
failure is reported as a warning, matching Git's post-publication semantics.

Git 2.36 or newer runs hooks through `git hook run`. Older POSIX Git executes
the configured traditional executable hook directly; older Windows Git fails
this optional SCM path closed. A missing, ambient, stale, malformed,
dead-owner, wrong-root, wrong-path, wrong-`HEAD`, wrong-ref, wrong-index,
wrong-tree, or wrong-blob marker never weakens ordinary claim persistence.

## Recovery Pattern

1. Read `STATUS.md` for the current handoff.
2. Read `agents/runtime/task_claims/*.json` for active claims and use
   `task_set_id`, `phase`, `step_index`, `step_total`, `progress_pct`, and
   `status_text` to pick the correct pane state.
3. Open the claim's `log_path` and `handoff_path`.
4. Continue in the claim's `worktree_path` and `branch`, or release the claim
   after writing an explicit handoff.
