---
title: Parallel Goal and Session Failure Audit
date: 2026-07-30
signal: fail
score: 42
tags:
  - owner-observation
  - multi-agent
  - goal-scope
  - session-isolation
  - automation
  - merge-integrity
---

# Parallel Goal and Session Failure Audit

## Bottom line

Agent Runtime has useful local safeguards, but it does not yet provide a hard
execution boundary for a goal or a hard ownership boundary for a session.
Today, a running taskset is resolved from the live work registry, claims are
stored in tracked source state without a session identity, and some recovery
paths stage every dirty file. Those choices explain the Owner-observed chain:

1. work discovered during a goal becomes eligible for the same run;
2. one session persists or imports another session's state;
3. sibling sessions observe the imported state as an unknown change;
4. each session attempts reconciliation, checkpointing, or duplicate work;
5. the reactions themselves become new foreign changes.

This is fixable. Git worktrees are a necessary checkout boundary, but they are
not sufficient. The runtime also needs immutable goal-run manifests, exclusive
session leases, commit provenance, foreign-state quarantine, atomic claims,
and a serialized integration authority.

## Owner observations

- A goal starts with a known taskset, but tasks or tasksets discovered later
  can be picked up instead of being reported and left for a new decision.
- Parallel sessions see, commit, pull, push, or otherwise reflect sibling work.
- A sibling change is reported as an unknown or out-of-session change, which
  stalls otherwise independent work.
- Multiple sessions then repeat the same diagnosis or implementation.
- Reconciliation of the repeated work creates another round of unknown changes.
- Worktree separation reduces file-level collision but does not prevent
  incompatible designs, shared branch movement, shared runtime-state commits,
  or duplicate semantic work.

The desired invariant is stronger than "different directories":

> One mutating session owns exactly one goal run, one immutable execution
> scope, one worktree, one branch, one lease, and one commit range. It may
> observe foreign state, but it may not stage, commit, push, revert, merge, or
> use that state as a reason to block unless a declared ownership boundary
> overlaps.

## Official Codex behavior and the Runtime responsibility

The Codex long-running-work documentation treats the first prompt as the goal
and completion criteria. Follow-up messages can refine constraints and the
agent can continue until the goal is achieved. Each chat has its own messages,
results, and goal. The Git worktree guidance recommends separate worktrees for
parallel tasks and explicitly warns against concurrent writes to the same
files.

References:

- <https://learn.chatgpt.com/docs/long-running-work>
- <https://learn.chatgpt.com/docs/environments/git-worktrees>

Those guarantees are chat- and checkout-level. They do not define an Agent
Runtime task membership snapshot, session-owned commit range, distributed
lease, or merge authority. The custom runtime must add those invariants.

## Current implementation findings

### 1. Goal identity is a mutable string, not a frozen run

- `scripts/agent_loop.py:67-92` stores only `LoopConfig.goal: str | None`.
- `scripts/goal_supervisor.py:96-148` reconstructs the latest run from the
  current day's JSONL file, indexes restart counts by goal text, and resumes by
  passing that text back to `agent_loop.py`.
- There is no `goal_run_id`, `session_id`, `scope_epoch`, `scope_hash`,
  `base_sha`, exact task/unit membership, or completion predicate.

Result: identical text can identify different attempts, changed registry state
can alter the work behind the same text, and a supervisor cannot prove that it
is resuming the same execution contract.

### 2. Running taskset membership is live and can grow

- `scripts/wave_dispatcher.py:146-179` enumerates all unit specs every time
  `select_units()` runs, then selects every current unit belonging to the
  requested taskset.
- A task or unit added after the goal starts is therefore eligible on the next
  plan/dispatch pass.
- `scripts/taskset_boundary_gate.py:128-159` activates only after a taskset
  records completion and allows same-taskset follow-on claims.

Result: the existing boundary gate can stop a later *different* taskset, but it
cannot prevent new work from entering the current taskset while the goal is
running.

### 3. The taskset boundary is repository-global, not goal/session-local

- `scripts/taskset_boundary_gate.py:68-80` loads every tracked claim visible in
  the checkout.
- `scripts/taskset_boundary_gate.py:110-159` compares every active claim with
  every completed scope without a `goal_run_id` or `session_id`.

Result: a valid sibling session can influence another session's boundary
decision. A safety gate can itself become a cross-session bottleneck.

### 4. Claims do not own a session or a goal run

- `scripts/task_claim_dispatcher.py:513-602` records task, instance, worktree,
  branch, taskset, and target files, but not a durable `session_id`,
  `goal_run_id`, scope hash, base SHA, fencing token, or owned commit range.
- Claim creation checks current records and then writes later
  (`scripts/task_claim_dispatcher.py:1120-1215`) without one canonical
  compare-and-swap transaction covering the conflict check and persistence.

Result: the runtime cannot prove who owns a branch mutation, distinguish stale
writers, or guarantee that two concurrent claim creates did not both pass the
same pre-write check.

### 5. Volatile runtime state is committed into source history

- Claim autocommit is enabled by default
  (`scripts/task_claim_dispatcher.py:63-69`).
- Claim JSON, handoff, and log files are committed immediately
  (`scripts/task_claim_dispatcher.py:1239-1255`) as protection against a
  sibling reset/clean incident.
- `scripts/parallel_worktree_gate.py:13-21` documents that linked worktrees see
  stale claim snapshots and makes the primary checkout authoritative.

Result: crash safety was obtained by advancing shared source history. Other
sessions then see runtime coordination records as source commits, and linked
worktrees disagree about the canonical active state.

### 6. Recovery can commit foreign files

- `scripts/agent_loop.py:165-188` implements dirty recovery with
  `git add -A` followed by a WIP commit.

Result: if a session is ever in a shared or contaminated worktree, the recovery
path can turn every visible foreign edit into that session's commit. This is
the opposite of session ownership.

### 7. Stop-hook scope is inferred, not owned

- `scripts/stop_hook_session_scope.py` infers mutations from transcript tool
  events and shell text.
- It compares inferred touched paths with the checkout's dirty paths and can
  return `dirty-state-unrelated-to-session`
  (`scripts/stop_hook_session_scope.py:400-414`).

This is useful noise reduction, but it is heuristic. It does not establish an
exclusive worktree/branch lease, commit provenance, or an authoritative owned
path set.

### 8. Planned footprints and merge gates remain bypassable

- Empty claim `target_files` produce a warning rather than an acquisition
  failure (`scripts/task_claim_dispatcher.py:454-472`).
- Path-level worktree separation cannot detect two independent component
  rewrites, schema/API incompatibility, generated-view ownership, or design
  token divergence.
- The local merge queue is substantially safer than direct merge, but a remote
  push or host setting can bypass local process unless required checks,
  protected gate files, and a gate attestation bound to the exact candidate SHA
  are enforced remotely.

### 9. Bounded loops are not durable idempotent workflows

The loop caps iterations, failures, dispatch count, and token budget per
process. It does not yet have a durable run/step ledger, idempotency keys,
effect receipts, a global retry budget, lease fencing, cancellation cascade,
or compensation records.

Result: process restart, supervisor retry, or duplicate dispatch can repeat an
external effect even when each individual process is locally bounded.

### 10. Green mechanical gates do not prove semantic integrity

The Bean Wiki parallel-work review demonstrated that ordinary CI can stay
green while integrated behavior regresses. Mechanical mergeability does not
prove navigation, responsive layout, design-system consistency, preserved
user flows, or a trustworthy visual baseline.

### 11. Registered tasksets are not immediately dispatch-resolvable

The deterministic registration path writes
`agents/project/work-items/TASKSET-DEFINITIONS.json`, but the current
`taskset_dispatcher` alias builder reads static code definitions and canonical
`agents/project/initiatives/TASKSET-*.md` records instead of that dynamic
registry. A newly registered taskset therefore passes work registration yet
`wave_dispatcher --taskset <new-id>` reports an unknown alias. Explicit unit
selection still plans correctly.

Result: producer and consumer disagree on the taskset registry. The remediation
taskset records this as a first-wave acceptance criterion so ordinary taskset
dispatch cannot start from an incomplete projection.

## Failure-mode and control matrix

| Failure mode | User-visible symptom | Required control | Current state |
| --- | --- | --- | --- |
| Mid-goal task inclusion | The agent keeps working after the intended set | Immutable goal-run membership and explicit scope transition | Missing |
| Cross-goal boundary bleed | One goal blocks because another completed | Scope gates keyed by goal run and session | Missing |
| Duplicate claim race | Two agents implement the same task | Atomic unique acquisition plus fencing token | Partial, non-atomic |
| Same branch in two sessions | Commits/pushes absorb sibling work | Exclusive session-to-worktree-to-branch lease | Partial |
| Foreign dirty state | Repeated "unknown changes" stalls | Foreign-state quarantine; block only on owned overlap | Heuristic only |
| Broad checkpoint staging | Sibling edits enter a WIP commit | Exact owned-path staging; prohibit `git add -A` | Unsafe path exists |
| Runtime/source coupling | Claims appear as foreign source commits | Untracked canonical runtime store plus serialized projections | Missing |
| Semantic overlap | Two clean diffs implement incompatible designs | Semantic domains, ownership map, contract tests | Partial |
| Stale writer | Expired session still commits/pushes | Lease renewal and monotonic fencing token | Missing |
| Duplicate external effect | Retry sends/publishes twice | Durable idempotency key and effect receipt | Missing |
| Retry storm | Supervisors repeatedly restart work | Global retry budget, jitter, circuit breaker | Partial per process |
| Cancellation leak | Parent stops but child agents continue | Run-scoped cancellation propagation | Missing |
| Remote gate bypass | Local checks pass but unverified SHA merges | Required remote queue and SHA-bound attestation | Partial |
| Gate self-weakening | A branch relaxes the gate it must pass | Base-owned protected gate policy | Missing/partial |
| Baseline laundering | Broken output becomes the new expected result | Independently governed baseline updates | Partial |
| Green but wrong UI | Tests pass while experience regresses | Semantic, visual, accessibility, and journey verification | Partial |

## Target architecture

### A. Immutable goal-run contract

Create a canonical `goal_run` record before mutating dispatch:

```json
{
  "goal_run_id": "GR-...",
  "session_id": "SES-...",
  "goal_text": "...",
  "scope_epoch": 1,
  "scope_hash": "sha256:...",
  "base_sha": "...",
  "allowed_taskset_ids": ["TASKSET-..."],
  "allowed_task_ids": ["TASK-..."],
  "allowed_unit_ids": ["UNIT-..."],
  "completion_predicate": "all frozen units verified and closed",
  "owner_approval_ref": "...",
  "status": "active"
}
```

- Freeze exact IDs and their relevant metadata hash at run start.
- Dispatch from this manifest, never from the live registry.
- Put newly discovered work into the planning outbox as a proposal.
- Do not claim it in the active run.
- Expand scope only with an explicit owner-approved transition that creates a
  new epoch and hash and re-runs dependency/conflict checks.
- Resume by `goal_run_id + scope_hash`, never by goal text alone.

### B. Exclusive session ownership

Maintain a canonical session lease outside tracked source state:

```json
{
  "session_id": "SES-...",
  "goal_run_id": "GR-...",
  "worktree": "/absolute/path",
  "branch": "codex/...",
  "base_sha": "...",
  "lease_expires_at": "...",
  "fencing_token": 17,
  "claim_ids": ["CLAIM-..."],
  "owned_paths": ["..."],
  "owned_domains": ["design-system/navigation"],
  "commit_range_start": "..."
}
```

- One mutating session maps to exactly one worktree and branch.
- A branch can have only one live owner.
- Every mutation, claim heartbeat, commit, push, and release presents the
  current fencing token.
- The session may only stage paths in its owned diff/footprint.
- The session may push only its owned branch and commits descended from its
  recorded base.
- Sibling refs and worktrees are read-only observations.

For local concurrency, the canonical lease store should live under the Git
common directory (for example `.git/agent-runtime/`) with OS locking and atomic
replacement. A later multi-host implementation can place the same CAS and
fencing contract in a central database. Tracked summaries may be projected by
one serialized orchestrator, but workers must not commit live coordination
state into product branches.

### C. Foreign-state quarantine

Classify visible changes:

- `owned`: created or modified by this session and within its lease;
- `expected_generated`: deterministic result owned by the integration actor;
- `foreign_observed`: belongs to a sibling session or ref;
- `overlap`: intersects an owned file or semantic domain;
- `unattributed`: cannot be mapped to any active or released lease.

Only `overlap` and `unattributed within the owned worktree` block. A
`foreign_observed` change must not be staged, committed, reverted, merged, or
used as a reason to halt unrelated work.

### D. Serialized integration

- Worker sessions never merge main or import sibling branches.
- Workers do not pull/rebase in the middle of execution.
- A single merge queue/orchestrator validates dependencies and integrates
  candidate SHAs.
- Revalidation against the latest base happens at queue time.
- Required remote checks verify an attestation bound to repository, base SHA,
  candidate SHA, task, goal run, gate bundle version, and result.
- Gate policy and baseline changes are evaluated using the protected base
  version and require explicit elevated review.

### E. Durable automation

- Persist run, step, attempt, idempotency key, lease, effect receipt, and
  cancellation state.
- Acquire a step lease with fencing before an effect.
- Write an intent before the effect and a receipt after it.
- On restart, reconcile receipts before retrying.
- Enforce a global attempt/time/cost budget with exponential backoff and
  jitter.
- Cascade cancellation from goal run to child agents and queued effects.
- Define compensation or manual-recovery instructions for non-reversible
  effects.

## Scope-transition protocol

Follow-up conversation must not silently mutate an active goal contract.

1. Classify a follow-up as one of:
   `context`, `constraint`, `scope_expansion`, `scope_replacement`, or
   `separate_goal`.
2. `context` and constraints that do not change membership may update notes.
3. A membership change creates a planning proposal and reports it.
4. Only an explicit owner decision creates a new `scope_epoch`.
5. The old epoch remains immutable and auditable.
6. No active worker can see new membership until the transition is committed.

This preserves conversational flexibility without converting every newly
mentioned task into execution authority.

## Delivery priority

### P0 — stop cross-session contamination

1. Freeze goal-run scope and resume by immutable identity.
2. Add atomic session/claim leases with fencing.
3. Enforce one session, one worktree, one branch.
4. Remove broad staging and tracked live-state autocommits.
5. Quarantine foreign observations and make stop/closeout ownership-aware.

### P1 — make integration and loops trustworthy

6. Make actual footprints and semantic domains mandatory.
7. Add durable idempotent run/step/effect state.
8. Require SHA-bound remote integration attestation.
9. Add semantic behavior, baseline, and gate-governance controls.

### P2 — prove the system under failure

10. Run race, crash, stale-lease, retry, cancellation, and incompatible-design
    chaos scenarios before broad adoption.

## Acceptance for the remediation program

- Adding a task or unit after a goal starts does not alter the active run.
- An owner-approved scope transition is the only way to change membership.
- Two simultaneous claim attempts for the same task/domain yield one winner.
- No two live sessions can own the same worktree or branch.
- A worker cannot stage, commit, push, or release with a stale fencing token.
- A sibling-only change neither enters the current commit nor blocks closeout.
- No runtime recovery path uses broad staging.
- Live coordination state does not advance a worker's source branch.
- Duplicate retries do not repeat an externally visible effect.
- Only the integration authority can import a worker commit into the protected
  branch.
- The exact candidate SHA has mechanical, semantic, and governance evidence.
- Chaos tests reproduce the current failure chain before the fix and prove it
  cannot recur afterward.

## Decision

Register one implementation taskset, **Autonomous Execution Integrity**, with
sequential P0 foundations and explicit parallelism only after ownership and
footprint gates exist. Planning/research work may remain parallel and
read-only; mutating work must use the frozen manifest and session lease.
