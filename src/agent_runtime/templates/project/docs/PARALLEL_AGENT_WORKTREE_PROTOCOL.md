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
tasks, missing instance/display metadata, malformed overlay contracts, and
missing handoff/log pointers. An out-of-`HEAD` working-tree overlay remains
visible as a reset/clean risk watch.

## Dispatch Pattern

```bash
python scripts/task_claim_dispatcher.py create --task-id TASK-EXAMPLE --agent-role lead-engineer --mode design --tag planning --tag no-ssot-write
git worktree add .worktrees/TASK-EXAMPLE -b codex/task-example-design-01 main
```

The create command writes the claim JSON, handoff, and log but leaves Git
`HEAD` unchanged. In a control repository where an SCM commit is separately
authorized, add `--commit-claim-artifacts`; that opt-in commits only those
three claim artifacts. `AGENT_RUNTIME_CLAIM_AUTOCOMMIT=1` remains an explicit
compatibility opt-in. Missing, false, or malformed environment values never
authorize a commit.

For an explicit claim-only commit, `claim_guard.py` creates a private mode
`0600` index from the starting `HEAD` after staging the claim artifacts in
the real index for visible recovery. Only the requested claim JSON, handoff,
and log enter that index; unrelated staged, partially staged, unstaged, and
untracked work stays outside the candidate tree.

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
blocks them. After publication, `post-commit` runs while the owned
`HEAD.lock` is still held, so Runtime-invoked hook work cannot switch symbolic
`HEAD` before the guard returns. Its failure is reported as a warning because
the sealed commit is already published; the lock is then released
immediately.

Git 2.36 or newer runs hooks through `git hook run`. Older POSIX Git executes
the configured traditional executable hook directly; older Windows Git fails
this optional SCM path closed. A missing, ambient, stale, malformed,
dead-owner, wrong-root, wrong-path, wrong-`HEAD`, wrong-ref, wrong-index,
wrong-tree, or wrong-blob marker never weakens ordinary claim persistence.

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
