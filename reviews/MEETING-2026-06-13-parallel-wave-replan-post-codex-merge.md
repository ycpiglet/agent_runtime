---
type: meeting
id: MEETING-2026-06-13-parallel-wave-replan-post-codex-merge
audience: owner
status: pass
signal: pass
score: 88
priority: High
tags: [planning-record, replan, plan-assumptions, parallel-wave, codex-merge]
---

# Parallel Wave Replan After Codex Merge (T3)

## Bottom Line

- Summary: `plan_assumption_gate --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION`
  reported 5 drift findings after the codex merges (#26, #28-#39) landed on
  `main` via PR #41. This record is the required T3 replan review before
  re-recording anchors and dispatching AR-500..507.
- Result: the plan direction survives; the build substrate changed. Wave
  execution work must now wire into `scripts/work.py` (2,665-line Work CLI),
  `WORK-SCHEMA.yml`, `TASKSET-DEFINITIONS.json`, `TASK-ID-RESERVATIONS.json`,
  and the agent-identity claim path (`record_claim_instance` in
  `task_claim_dispatcher.py`).
- Boundary: replan only. No task scope is closed or reopened here; anchors are
  re-recorded against this record immediately after registration.

## Signal

| Drift Finding | Cause | Plan Impact |
| --- | --- | --- |
| anchor-hash-changed `scripts/task_claim_dispatcher.py` | #37 added `record_claim_instance` + instance-attributed pane events at claim creation | AR-503/AR-507 now have instance IDs to enforce; AR-500 wiring must preserve the spawn-record call order |
| anchor-appeared `agents/project/WORK-SCHEMA.yml` | #28 work schema SSoT gate | AR-515 builds on it; wave units must stay schema-valid |
| anchor-appeared `agents/project/work-items/TASKSET-DEFINITIONS.json` | #37 taskset registry | Done: METADATA-ANALYTICS and PARALLEL-WAVE-EXECUTION migrated off the hardcoded list in PR #41 |
| anchor-appeared `agents/project/work-items/TASK-ID-RESERVATIONS.json` | #26 reservation ledger | 500-band reservation note in BACKLOG can now be recorded retroactively in the ledger |
| anchor-appeared `scripts/work.py` | #29-#36 Work CLI (new/verify/close/criteria/assign/split/now) | AR-501/AR-502 dispatch and closeout should call Work CLI surfaces instead of reimplementing them |

## Insight

- The deferred-revalidation design worked as intended: registration happened
  pre-merge, dispatch was blocked until the merged reality was inspected, and
  no implementation was built against stale assumptions.
- `work.py verify/close` plus the identity registry give AR-507 its enforcement
  primitives for free: claims carry `agent_instance_id`, so verifier-not-equal-
  worker is a comparison of instance IDs, not roles.
- The dispatcher edit surface for AR-500 wiring is small (claim create path),
  so the footprint conflict gate hooks in after reservation/claim build and
  before `record_claim_instance`/`append_event`.

## Decision

- Decision: proceed with TASKSET-AR-PARALLEL-WAVE-EXECUTION dispatch on the
  post-merge substrate; re-record all 8 anchors against this design record.
- Decision: execution order stays AR-500 residual (dispatcher wiring) ->
  AR-503 (claim-first) -> AR-501 (wave dispatcher) -> AR-502 (merge queue) ->
  AR-506 (lifecycle defaults) -> AR-507 (cross-verification gate); these share
  the dispatcher/claims footprint and run as a sequential lane.
- Decision: AR-505 (worktree lifecycle gate) and the independent lanes
  (AR-509..513 release/hygiene/overlay, AR-514..519 metadata analytics) may run
  in parallel worktrees because their `target_files` footprints do not overlap
  the dispatcher lane.
- Decision: all merges to `main` go through PRs with W4b independent
  verification; direct push to `main` stays disallowed.

## Action Board

| Status | Action | Owner | Evidence |
| --- | --- | --- | --- |
| Done | T1 drift check after codex merge | lead-engineer | `plan_assumption_gate --check` findings=5 |
| Done | Taskset registry migration (PR #41) | lead-engineer | `TASKSET-DEFINITIONS.json` orders 513-514 |
| Next | Re-record 8 anchors against this record | lead-engineer | `PLAN-ASSUMPTIONS.json` |
| Next | Dispatch AR-500 residual wiring | lead-engineer | claim + worktree per W0-W6 |
| Watch | 500-band retroactive reservation entries | lead-engineer | `TASK-ID-RESERVATIONS.json` |

## Risks / Blockers

- Risk: `work.py` is large and new; wave dispatcher work that bypasses it will
  fork lifecycle logic. Mitigation: treat Work CLI as the only mutation surface
  for unit verify/close during AR-501/AR-502.
- Risk: parallel lanes touching generated views (`BACKLOG-BOARD.md`,
  `WORK-ITEM-CLASSIFICATION.*`, `reviews/INDEX.md`) will conflict on merge.
  Mitigation: regenerate in the integration step of each PR, never hand-merge.

## Next Steps

- Run `plan_assumption_gate record` with the 8 anchors and this design record.
- Confirm `plan_assumption_gate --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION`
  returns findings=0.
- Start AR-500 residual under a fresh claim with instance attribution.
