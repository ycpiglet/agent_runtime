---
schema_version: agent-runtime-review/v1
id: RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize
title: TASK-AR-655 Owner-Authorized Stale Claim Terminalization
date: 2026-08-03
created_at: 2026-08-03T13:49:49+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: recovery
reviewer: owner-authorized-recovery
reviewer_role: owner
status: applied
signal: recovered
verdict: RECOVERED
priority: P1
recovery_scope: single-claim
recovery_authority: owner-explicit-approval
recovered_by: ycpiglet <68498184+ycpiglet@users.noreply.github.com>
recovered_at: 2026-08-03T13:49:49+09:00
before_sha256: 96f7d3d505cd9774e136f3a1bdc3e2c270b2c2aa11a299f6f6e04ddeb9cd59c1
after_sha256: 42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5
w4b_acceptance: false
release_authorized: false
follow_up_task: TASK-AR-659
tags: [recovery, task-ar-655, legacy-claim, lease-expiry, orchestrator-claim, owner-authority, deadlock]
---

# TASK-AR-655 owner-authorized stale claim terminalization

## Bottom Line

Exactly one claim — `CLAIM-20260803-002651-task-ar-655-5f27` — was
terminalized from `claimed` to `expired` under explicit Owner authority. It was
**not** deleted, **not** released, and **not** completed. No unit acceptance, no
W4b approval, and no release authorization is implied or granted by this
record.

The claim's lease expired at `2026-08-03T08:26:51+09:00`. At recovery time
(`2026-08-03T13:49:49+09:00`) it was **19,372 seconds (~5.4 h) overdue**, far
beyond the 600 s reaper grace, yet it still presented as an active claim to
every runtime consumer.

## Why no automated path existed

The stale claim was reachable by no registered command. Four independent
blockades, all verified against the source before recovery:

| Path | Outcome | Evidence |
|---|---|---|
| Natural expiry | Status stays `claimed` regardless of deadline | `expires_at` 08:26:51 vs now 13:49:49 |
| `claim_reaper.py` | Unconditional skip: `mode == "orchestrator"` is tested **before** liveness | `scripts/claim_reaper.py:110-111`; dry-run reported `reason: orchestrator-claim`, `would_reap: 0` |
| `heartbeat` / `renew` | Rejected — claim predates the mutation fields | `scripts/task_claim_dispatcher.py:2581-2583`; observed `claim mutation revision is invalid` on both |
| New claim | `task already has an active claim` (655) and `task set already has an active claim` (siblings) | `scripts/task_claim_dispatcher.py:2075`, `:2144`, `:759` |

No `expire`, `terminalize`, or `bootstrap` subcommand exists:
`claim_lease.py` exposes `{acquire, release, heartbeat}` and
`task_claim_dispatcher.py` exposes `{create, heartbeat, renew, projection,
release}`.

The consequence is a genuine deadlock: one stale claim simultaneously blocked
resuming TASK-AR-655 **and** claiming any sibling task in
`TASKSET-AR-V080-OPERABILITY-HARDENING`, including the recovery task needed to
fix the defect.

## Before digest

```
path        agents/runtime/task_claims/CLAIM-20260803-002651-task-ar-655-5f27.json
sha256      96f7d3d505cd9774e136f3a1bdc3e2c270b2c2aa11a299f6f6e04ddeb9cd59c1
size        9983 bytes
mtime       2026-08-03 08:22:50 +0900
status      claimed
mode        orchestrator
expires_at  2026-08-03T08:26:51+09:00
mutation_revision  absent
scope_binding      absent
```

Both rejection probes were executed **before** the mutation and left the digest
unchanged at `96f7d3d5…`, confirming the commands fail closed without partial
writes.

## Mutation applied

The mutation mirrors the shape of `scripts/claim_reaper.py::_reap_locked`
(lines 162-169) so the terminal record is indistinguishable in structure from an
ordinary reap, with authority honestly attributed to the Owner rather than to
`claim_reaper`. Written via the shared durable primitive
`atomic_io.write_json_atomic` (temp → fsync → atomic rename).

```
status                              claimed -> expired
recovered_from_status               claimed
reaped_at                           2026-08-03T13:49:49+09:00
reaped_by                           owner-manual-recovery
reaped_reason                       lease-expired
updated_at                          2026-08-03T13:49:49+09:00
recovered_at                        2026-08-03T13:49:49+09:00
recovered_by                        ycpiglet <68498184+ycpiglet@users.noreply.github.com>
recovery_authority                  owner-explicit-approval
recovery_scope                      single-claim
recovery_independent_evidence_refs  [this document]
```

The `recovered_at` / `recovered_by` / `recovery_reason` field names reuse the
recovery vocabulary already registered in `scripts/state_sync_gate.py:386`.

Preserved untouched: `claim_id`, `task_id`, `claimed_at`, `expires_at`,
`phase` (`worker-w4a-type-strict-pointer-complete`), `progress_pct` (99),
`step_index`, `defect_signatures`, `compound_refs`, `target_files`.

## After digest and verification

```
sha256                 42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5
status                 expired
_is_active             False   (task / task-set exclusivity released)
in ACTIVE_CLAIM_STATUS False   (footprint conflict released)
files changed          1 (this claim JSON only)
```

Fail-closed guards enforced by the recovery script: exact `claim_id` match,
exact before-digest match, `status == "claimed"` precondition, and a refusal to
terminalize a claim whose lease has not actually expired.

## Known residue — not fixed here

`claim_reaper.py` still reports this claim under `skipped` with reason
`orchestrator-claim`, because `_is_orchestrator` short-circuits before the
status and liveness checks. The claim is now correctly inactive to every
consumer that reads status, but the reaper's own report remains misleading.
This is the defect itself, not a side effect of the recovery, and is in scope
for the follow-up task.

## Explicitly NOT granted

- Unit `UNIT-TASK-AR-655-001` is **not** accepted.
- The W4b verdict remains `REVISE — P1: 1`; its blocking finding stands.
- No release, tag, push, publish, or deploy authorization.
- No consumer project was touched.
- The Scribe blocker remains in force.

## Follow-up

`TASK-AR-659` will implement owner-bound legacy claim bootstrap/rotation
RED-first, so this class of stale claim has a registered command path and never
again requires a manual mutation. The recurring defect family reached its 4th
instance before this recovery; a Compound record is required to close it.
