---
title: Work Split Command
date: 2026-06-12
signal: pass
score: 92
tags: [work-cli, split, planning-proposal, task-ar-372]
---

# Work Split Command

## Bottom Line

`scripts/work.py split <task>` adds a proposal-only task-to-unit decomposition
surface to the Work CLI. It detects whether a task already has canonical unit
files and, only when it does not, writes a B-mode proposal containing proposed
worker-ready unit specs.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Split proposal | pass | `tests/test_work_split.py` creates a B-mode proposal for an unsplit task |
| Existing-unit pass | pass | existing canonical units return pass without outbox writes |
| Source immutability | pass | tests assert the source task text is unchanged |
| Unit creation guard | pass | tests assert no canonical unit directory is created |
| Missing task guard | pass | missing task returns nonzero and writes nothing |
| Self-hosting verification | pass | `UNIT-TASK-AR-372-009` verified and closed by Work CLI commands |

## Insight

- The command deliberately does not allocate display IDs or create unit files.
  It proposes unit specs that can be reviewed and applied later.
- The first split heuristic maps each acceptance criterion to a proposed unit,
  capped at five proposed units, and carries task verification commands forward
  when they are executable.
- An internal readiness check verifies the proposed unit fields before writing
  the proposal, which keeps the generated draft aligned with the unit readiness
  contract without pretending the draft is canonical.

## Decision

- Decision: `work split` writes no canonical task or unit changes.
- Decision: proposal outputs use `mode: B`, `status: proposed`,
  `action_type: plan_update`, and `proposal_output: plan`.
- Decision: approved apply, ID reservation, automatic dispatch, and Work
  Explorer UI remain separate records.

## Action Board

| Item | Status | Note |
| --- | --- | --- |
| `work split` CLI | done | proposes unit specs for unsplit tasks |
| Proposal JSON/draft output | done | unsplit tasks write outbox and draft records |
| Unit creation guard | done | command does not create canonical unit files |
| `UNIT-TASK-AR-372-009` | done | verified by `work verify`, closed by `work close` |

## Risks / Blockers

- The split heuristic is intentionally simple and deterministic. Richer
  decomposition should use the same proposal boundary with planner model input.
- Existing units suppress new split proposals for now; future work can add a
  force/re-split mode behind explicit approval.

## Next

- Add approved-apply behavior only after proposal review semantics and ID
  reservation boundaries are settled.
- Work Explorer UI and stats views should consume these proposal records rather
  than bypassing the Work CLI contract.
