---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
work_uid: 8da7c6f1-0f2b-4d1e-b333-fd8384385b3d
kind: taskset
id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
parent_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
status: active
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Freeze goal-run membership, isolate every writer session, move live coordination out of source history, make effects idempotent, and prove serialized integration under concurrency and failure.
---

# Autonomous Execution Integrity

## Goal

- Freeze goal-run membership, isolate every writer session, move live coordination out of source history, make effects idempotent, and prove serialized integration under concurrency and failure.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-655` | Freeze goal-run scope and require attested transitions |
| `TASK-AR-656` | Bind dispatch, loops, and supervision to a frozen run |
| `TASK-AR-657` | Make session and claim ownership atomic and durable |
| `TASK-AR-658` | Enforce session-owned SCM and quarantine foreign state |
| `TASK-AR-659` | Make footprints, semantic domains, and dependencies mandatory |
| `TASK-AR-660` | Make automation loops durable and idempotent |
| `TASK-AR-661` | Seal integration with SHA-bound remote attestation |
| `TASK-AR-662` | Strengthen semantic verification and baseline governance |
| `TASK-AR-663` | Prove concurrent-session safety and roll out enforcement |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-655-001` | `TASK-AR-655` | Implement immutable GoalRun storage and membership hashing |
| `UNIT-TASK-AR-655-002` | `TASK-AR-655` | Add explicit scope amendment and registration dependency aliases |
| `UNIT-TASK-AR-656-001` | `TASK-AR-656` | Select and claim only frozen goal-run members |
| `UNIT-TASK-AR-656-002` | `TASK-AR-656` | Resume the exact run and stop on frozen completion |
| `UNIT-TASK-AR-657-001` | `TASK-AR-657` | Build the canonical control-plane store and fenced lease primitive |
| `UNIT-TASK-AR-657-002` | `TASK-AR-657` | Move live claims out of source history and project compatibility views |
| `UNIT-TASK-AR-658-001` | `TASK-AR-658` | Guard every worker mutation and remove broad staging |
| `UNIT-TASK-AR-658-002` | `TASK-AR-658` | Make dirty, stop, and closeout decisions session-local |
| `UNIT-TASK-AR-659-001` | `TASK-AR-659` | Enforce planned and actual ownership across files and domains |
| `UNIT-TASK-AR-660-001` | `TASK-AR-660` | Persist run steps, effect receipts, retries, and cancellation |
| `UNIT-TASK-AR-661-001` | `TASK-AR-661` | Require provenance and exact-SHA attestation in the merge queue |
| `UNIT-TASK-AR-662-001` | `TASK-AR-662` | Add semantic integration and independent baseline controls |
| `UNIT-TASK-AR-663-001` | `TASK-AR-663` | Run chaos scenarios, migrate state, and stage enforcement |

## Execution Contract

- The taskset is planning-complete but not authorized for blind parallel
  dispatch.
- Mutating execution starts from the frozen unit list in this plan. Work
  registered later is discovery input only until an owner-approved scope
  revision exists.
- One worker session owns one claim, worktree, branch, lease, and commit range.
  A worker must not absorb, merge, rebase, stage, commit, push, revert, or
  close over a sibling session's state.
- Until `UNIT-TASK-AR-657-001` and `UNIT-TASK-AR-658-001` are implemented and
  verified, dispatch uses cascade mode. Parallel waves describe the target
  steady-state and may run concurrently only when their file and semantic
  footprints remain disjoint after latest-base revalidation.
- New follow-up work is recorded in the planning outbox and reported at the
  current frozen boundary. It does not automatically join this taskset run.
- Only the integration authority may import worker commits into the protected
  branch.

## Dependency Waves

The explicit-unit wave planner produced the following zero-cycle,
zero-deferral DAG:

| Wave | Units | Purpose |
| --- | --- | --- |
| 1 | `UNIT-TASK-AR-657-001` | Canonical transactional runtime-state store and fencing |
| 2 | `UNIT-TASK-AR-655-001` | Immutable GoalRun model on that store |
| 3 | `UNIT-TASK-AR-655-002`, `UNIT-TASK-AR-657-002` | Scope transition/registration fixes and live-claim migration |
| 4 | `UNIT-TASK-AR-656-001` | Frozen-scope dispatch and claim validation |
| 5 | `UNIT-TASK-AR-656-002`, `UNIT-TASK-AR-659-001` | Exact-run supervision and mandatory ownership footprints |
| 6 | `UNIT-TASK-AR-658-001` | Session-owned SCM boundary |
| 7 | `UNIT-TASK-AR-658-002`, `UNIT-TASK-AR-660-001` | Foreign-state quarantine and durable idempotent loops |
| 8 | `UNIT-TASK-AR-661-001` | Serialized integration and exact-SHA attestation |
| 9 | `UNIT-TASK-AR-662-001` | Semantic verification and baseline governance |
| 10 | `UNIT-TASK-AR-663-001` | Chaos proof, migration, shadow mode, and rollout |

Wave 3, Wave 5, and Wave 7 contain the only planned parallel pairs. They have
disjoint declared target files. The dispatcher must recheck actual footprints,
semantic domains, latest base, and dependency state before enabling parallel
mode.

## Priority and Exit Gates

### P0 foundation

`TASK-AR-657`, `TASK-AR-655`, `TASK-AR-656`, `TASK-AR-659`, and `TASK-AR-658`
must land in dependency order. P0 is complete only when:

- late-added work cannot enter a sealed run;
- simultaneous ownership acquisition has exactly one winner;
- claim lifecycle leaves source `HEAD` and status unchanged;
- broad staging is impossible;
- sibling-only state neither enters a commit nor blocks closeout;
- stale fencing tokens fail at mutation and release.

### P1 automation and integration

`TASK-AR-660`, `TASK-AR-661`, and `TASK-AR-662` add durable effect receipts,
global retry/cancellation state, exact-SHA remote evidence, and semantic
verification. P1 is complete only when a restarted process cannot duplicate an
effect and a candidate cannot reuse, self-weaken, or launder verification
evidence.

### Rollout proof

`TASK-AR-663` must reproduce the current reciprocal unknown-change chain before
the fix and prove it absent afterward. Enforcement progresses through observe,
warn, block-new, and block-all stages. Any P0 race, ownership false positive,
or rollback data-loss case stops rollout.

## Known Registration Gap

Registration successfully wrote the dynamic taskset registry, task records,
unit specs, and plan-assumption snapshot. On the current base,
`wave_dispatcher --taskset TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY` still
fails because `taskset_dispatcher` does not resolve the dynamic registry used
by `work.py new`. Explicit-unit planning works and produced the waves above.
Fixing that producer-consumer mismatch is an acceptance criterion of
`UNIT-TASK-AR-655-002`; it must be resolved before normal taskset dispatch.

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
- `python scripts/work_schema_gate.py --items --check`
- `python scripts/conversation_work_audit.py --check`
- `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY`
- explicit-unit `python scripts/wave_dispatcher.py --plan --json ...` until the
  registered-taskset lookup acceptance criterion is implemented
