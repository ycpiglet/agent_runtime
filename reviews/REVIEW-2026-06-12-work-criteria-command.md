---
title: Work Criteria Command
date: 2026-06-12
signal: pass
score: 94
tags: [work-cli, criteria, planning-proposal, task-ar-372]
---

# Work Criteria Command

## Bottom Line

`scripts/work.py criteria <id>` now provides the first proposal-only B-mode
planner tool in the Work CLI. It evaluates whether acceptance criteria are
backed by executable verification commands and writes proposal records only
when gaps exist.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Gap proposal | pass | `tests/test_work_criteria.py` creates a B-mode proposal for unverifiable criteria |
| No-gap pass | pass | executable verification returns pass without outbox writes |
| Source immutability | pass | tests assert the source unit text is unchanged |
| Missing work guard | pass | missing work returns nonzero and writes nothing |
| B-mode boundary | pass | output is limited to `agents/planning/outbox/` and `agents/planning/drafts/` |
| Self-hosting verification | pass | `UNIT-TASK-AR-372-007` verified and closed by Work CLI commands |

## Insight

- The command deliberately does not invent final criteria or mutate task/unit
  records. It creates an inspectable planning proposal that can be approved and
  applied by a later bounded path.
- The first heuristic is intentionally simple: if a work item has acceptance
  criteria but no executable verification command, the criterion is
  unverifiable and proposal-worthy.
- This is a deterministic bridge toward the Owner request for context-aware
  criteria generation without bypassing B-mode review.

## Decision

- Decision: `work criteria` writes no canonical work item changes.
- Decision: proposal outputs use `mode: B`, `status: proposed`,
  `action_type: plan_update`, and `proposal_output: plan`.
- Decision: LLM-backed criteria generation and approved apply behavior remain
  future units; this unit only establishes the proposal contract and guardrails.

## Action Board

| Item | Status | Note |
| --- | --- | --- |
| `work criteria` CLI | done | evaluates criteria coverage |
| Proposal JSON/draft output | done | gap cases write outbox and draft records |
| Source immutability tests | done | source work item is unchanged |
| `UNIT-TASK-AR-372-007` | done | verified by `work verify`, closed by `work close` |

## Risks / Blockers

- The coverage heuristic is coarse: one executable verification command can
  satisfy all criteria for now. Richer criterion-to-command mapping belongs in a
  later planner model-backed unit.
- The command writes proposals only for gaps; it does not perform approved
  apply or mutate canonical records.

## Next

- Continue with proposal-gated `split` and `assign` tools as separate units.
- Later criteria work can add richer command-to-criterion matching and optional
  LLM-suggested verification commands behind the same B-mode boundary.
