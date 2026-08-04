---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-659-legacy-claim-bootstrap-t3-replan
title: TASK-AR-659 Legacy Claim Bootstrap Dispatch T3 Replan
date: 2026-08-03
created_at: 2026-08-03T14:35:00+09:00
task_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: owner-manual-recovery
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ACCEPT_TASK_AR_659_DISPATCH_AND_REANCHOR
priority: P1
defect_signature: defect:expired-orchestrator-claim-has-no-registered-recovery-path
recurrence_status: fourth_recurrence_in_claim_authority_family
post_green_compound_obligation: recurrence_count_4
release_authorized: false
predecessor_ref: reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
blocking_finding_ref: reviews/W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
tags: [task-ar-659, t3-replan, legacy-claim, claim-authority, reanchor, dispatch]
---

# TASK-AR-659 legacy claim bootstrap dispatch T3 replan

## Bottom Line

`ACCEPT` dispatch of TASK-AR-659 into
`TASKSET-AR-V080-OPERABILITY-HARDENING` and re-record the drifted t0 anchors.

The taskset's plan assumptions were anchored before TASK-AR-655 implemented
across the claim-authority surface. 29 anchors now report
`anchor-hash-changed`. The drift is **expected implementation progress by the
taskset's own in-flight task**, not an invalidated premise: every drifted
anchor is a file TASK-AR-655 declared in its own `target_files`.

The taskset's governing premise is unchanged — keep long-running claims
truthful and make expiry consistent across every consumer. TASK-AR-659
narrows that premise rather than replacing it.

## Why the anchors drifted

All 29 drifted anchors fall into three groups, all owned by TASK-AR-655:

| Group | Examples | Cause |
|---|---|---|
| Claim authority | `scripts/task_claim_dispatcher.py`, `claim_store.py`, `claim_lease.py`, `claim_reaper.py`, `deadlock_watchdog.py` | AR-655 lease/heartbeat/renew and liveness-classifier work |
| Consumers of liveness | `state_sync_gate.py`, `parallel_worktree_gate.py`, `worktree_lifecycle_gate.py`, `ui_state.py` | AR-655 shared-classifier propagation |
| Mirrors and tests | `src/agent_runtime/templates/project/scripts/**`, `tests/test_claim_*.py`, `tests/fixtures/host/agent_runtime.lock.json` | template mirror contract plus the RED/GREEN suites |

No anchor drifted because of an external actor, a consumer project, or an
unreviewed change.

## What TASK-AR-659 adds and why it cannot wait

On 2026-08-03 `CLAIM-20260803-002651-task-ar-655-5f27` expired and became
unreachable by every registered command at once: the reaper skips
`mode == "orchestrator"` before testing liveness
(`scripts/claim_reaper.py:110`), `heartbeat` and `renew` reject a claim that
predates `mutation_revision` / `scope_binding`
(`scripts/task_claim_dispatcher.py:2581`), replacement claims are refused by
task and task-set exclusivity (`:2075`, `:2144`, `:759`), and no
`expire`/`terminalize`/`bootstrap` subcommand exists anywhere.

One stale claim therefore blocked both resuming its own task **and** claiming
the task needed to fix it. It cleared only through an Owner-authorized manual
JSON mutation, recorded in the predecessor document. That manual step is
precisely what must not be required again, so TASK-AR-659 belongs inside this
taskset and ahead of AR-655's re-verification.

## Second gap found during dispatch

Creating the TASK-AR-659 worktree surfaced a related hole. The claim-store
outer marker lives in the per-worktree git admin directory, so every new
worktree starts `migration-required`. The only caller of
`claim_store.adopt_legacy_store()` is `src/agent_runtime/sync.py`, which
requires a consumer `agent_runtime.yml` that this repository does not have.
A new worktree in agent_runtime itself therefore has an unusable claim store
and **no registered activation command** — the same defect shape as the
unreachable claim, one level up.

Activation was performed for `.worktrees/TASK-AR-659` by calling the
registered `adopt_legacy_store()` function directly. This is added to
UNIT-TASK-AR-659-001 as an additional RED rather than left as tribal
knowledge.

## Plan assumptions after amendment

1. Claim authority stays local; no network or distributed lease is introduced.
2. Recovery is owner-bound: an unidentified caller is refused.
3. Recovery never fabricates progress — terminalize is not release, not
   completion, and not unit acceptance.
4. A live claim is never terminalizable by any new command.
5. The reaper classifies by status and liveness; mode alone never
   short-circuits the decision.
6. Every new surface is mirrored into the runtime template and the host lock
   is regenerated.

## Decision

- `ACCEPT` TASK-AR-659 dispatch into the taskset.
- Re-record the 29 drifted anchors against this design record.
- TASK-AR-655 stays `in_progress` and unaccepted; its W4b `REVISE — P1 1`
  stands and is re-verified only after TASK-AR-659 clears it.
- A Compound record is mandatory before TASK-AR-659 closeout: this is the 4th
  recurrence in the claim-authority defect family.
- No release, tag, push, publish, or deploy authorization is granted.
