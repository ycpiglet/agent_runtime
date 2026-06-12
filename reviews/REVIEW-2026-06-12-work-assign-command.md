---
title: Work Assign Command
date: 2026-06-12
signal: pass
score: 93
tags: [work-cli, assign, planning-proposal, task-ar-372]
---

# Work Assign Command

## Bottom Line

`scripts/work.py assign <id>` adds a proposal-only assignment recommender to
the Work CLI. It recommends team and owner metadata from local routing context,
includes active claim workload counts, and writes B-mode proposal records only
when assignment metadata is incomplete.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Assignment proposal | pass | `tests/test_work_assign.py` creates a B-mode proposal when team/owner metadata is missing |
| Explicit assignment pass | pass | explicit team and owner return pass without outbox writes |
| Source immutability | pass | tests assert the source unit text is unchanged |
| Claim boundary | pass | tests assert `agents/runtime/task_claims/` is not created |
| Missing work guard | pass | missing work returns nonzero and writes nothing |
| Self-hosting verification | pass | `UNIT-TASK-AR-372-008` verified and closed by Work CLI commands |

## Insight

- The command deliberately stops at recommendation and proposal output. It does
  not create task claims or dispatch workers; that remains behind approved
  apply/dispatcher paths.
- The first assignment heuristic is deterministic and intentionally simple:
  script/runtime/test targets route to `agent-runtime-core`, governance/security
  language routes to the safety team, release language routes to release
  integrity, evaluation language routes to evaluation, and planning language
  routes to planning-office.
- Active claim counts are included as context for workload-aware decisions, but
  they do not block proposal creation in this slice.

## Decision

- Decision: `work assign` writes no canonical work item changes.
- Decision: proposal outputs use `mode: B`, `status: proposed`,
  `action_type: plan_update`, and `proposal_output: plan`.
- Decision: approved apply, automatic dispatch, WIP enforcement, and LLM-backed
  routing remain future units.

## Action Board

| Item | Status | Note |
| --- | --- | --- |
| `work assign` CLI | done | recommends team/owner metadata |
| Proposal JSON/draft output | done | missing assignment writes outbox and draft records |
| Claim creation guard | done | command does not write task claims |
| `UNIT-TASK-AR-372-008` | done | verified by `work verify`, closed by `work close` |

## Risks / Blockers

- The rule set is heuristic and should be tuned once `work stats` and assignment
  outcomes provide real data.
- The command proposes assignment metadata only; it does not enforce WIP limits
  or claim ownership by itself.

## Next

- Continue with proposal-gated `split` as the remaining AI planner tool surface.
- Later assignment work can add skill-map scoring, WIP limits, saved views, and
  approved apply behavior behind the same B-mode boundary.
