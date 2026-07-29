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

## Continuity Source Selection

A present `STATUS.md` or `agents/lead_engineer/STATUS.md` remains the primary
continuity source and must contain an existing resume marker. A malformed
present status file cannot be bypassed by a pointer.

When both status candidates are absent, the only fallback is
`agents/project/NEXT-SESSION-POINTER.yml` plus every active claim's handoff and
log sidecars. The pointer must use the canonical schema, contain no placeholder
values, be at least as fresh as every active non-overlay claim heartbeat, list
exactly those claim paths, and contain exactly one full current-agent record
per claim. Missing, malformed, stale, duplicate, extra, partial, or mismatching
pointer state blocks.

After claim creation, the serial projection owner runs:

```bash
python scripts/task_claim_dispatcher.py projection --claim-id CLAIM-ID --json
```

The emitted record includes claim, agent, team, pane, task, unit, task-set,
phase/progress/step, worktree/branch, sidecar, and heartbeat fields. Projection
is read-only: neither claim creation nor this command edits the pointer or
changes Git `HEAD`. Doctor validates a structurally usable standby pointer
before first work and reports the effective `status+sidecars` or
`pointer+sidecars` path.

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
then opens the actual symbolic `HEAD` file without following a symlink and
keeps that regular-file descriptor open through publication. Its device,
inode, link count, and exact `ref: <authorized-branch>` bytes form the
cross-process `HEAD` identity seal. The guard installs a mode-`0700` private
`reference-transaction` hook context and asks Git to run
`update-ref --create-reflog HEAD <new> <old>` in the actual worktree context.
While Git owns the actual worktree-specific `HEAD.lock`, the private prepared
hook requires the `HEAD` path to retain the opened identity, requires the real
symbolic `HEAD` to name the originally authorized branch, and requires the
transaction to contain exactly the sealed `HEAD` and branch old/new
transitions. It repeats those checks after delegating the repository's
configured `reference-transaction` hook and aborts on any mismatch. Git's own
ref transaction therefore performs the old-OID compare-and-swap and records
both the shared branch reflog and the normal or linked worktree's actual
`logs/HEAD` transition.

Repository-local `GIT_*` redirectors are removed before the transaction.
Hooks and `commit-tree` always use the real worktree context; the private
context supplies only the guarded reference hook. Marker, index, message,
private-hook, and owned lock files are removed on every exit. A pre-existing
`HEAD.lock` is never removed and makes the transaction fail closed. Failure
leaves the claim artifacts staged so the ordinary gate blocks them.

After Git publishes and releases its locks, Runtime immediately acquires its
own actual worktree `HEAD.lock`. Under that new lock it requires the path's
current device and inode to equal the still-open pre-publication descriptor,
then verifies the symbolic ref, published commit, branch reflog, and
worktree-local `HEAD` reflog before running `post-commit`. A Git lockfile
rewrite, including an equal-OID `A -> B -> A` symbolic round trip, replaces or
unlinks the held inode and therefore cannot masquerade as an unchanged
`HEAD`. Lock contention or any identity/state mismatch returns
`ok=false`, `committed=true`, and
`publication_state=published_unverified`, skips `post-commit`, and never
auto-retries. The Runtime-invoked hook runs while the owned lock is held, so
it cannot switch symbolic `HEAD`. Its failure is reported as a warning
because the sealed commit and both reflogs are already published; the lock
and held descriptor are then released immediately.

Git 2.36 or newer runs hooks through `git hook run`. Older POSIX Git executes
the configured traditional executable hook directly. The private hook uses
the same absolute Python interpreter that started Runtime. Explicit claim SCM
is enabled only on POSIX platforms that provide `O_NOFOLLOW`; Windows and
other unsupported identity primitives fail before ref publication. Default
working-tree claim persistence remains cross-platform and does not enter this
transaction.

The identity seal protects normal Git ref operations, which use lockfile
replacement. Repository hooks execute with the user's authority and are
trusted code: they may observe or veto the reference transaction, but must not
rewrite `HEAD` or refs. A same-privilege process that edits Git administrative
files in place instead of using Git's lockfile protocol is outside this
cooperative-concurrency boundary. A missing, ambient, stale, malformed,
dead-owner, wrong-root, wrong-path, wrong-`HEAD`, wrong-ref, wrong-index,
wrong-tree, or wrong-blob marker never weakens ordinary claim persistence.

## Unit Dispatch Selection

Task-set plan/start dispatches only runnable units. A single `in_progress`
unit wins; otherwise a runnable task-level `unit_spec` is canonical, followed
by `worker_ready`/legacy `ready`, then `planned`. Historical `blocked`,
failed, cancelled, rejected, refinement-required, review, and completed units
are never fallback work. Multiple in-progress units, unknown statuses, a
missing canonical unit path, or a task with no runnable unit stop before a
claim command is emitted.

## Recovery Pattern

1. Read `STATUS.md` for the current handoff.
2. Read `agents/runtime/task_claims/*.json` for active claims and use
   `task_set_id`, `phase`, `step_index`, `step_total`, `progress_pct`, and
   `status_text` to pick the correct pane state.
3. Open the claim's `log_path` and `handoff_path`.
4. Continue in the claim's `worktree_path` and `branch`, or release the claim
   after writing an explicit handoff.
