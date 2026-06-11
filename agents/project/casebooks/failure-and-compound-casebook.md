# Failure and Compound Casebook

## Purpose

This casebook is the query surface for repeated failures and compound issues.
It does not replace `agents/lead_engineer/compound_log.md`; it indexes entries
into a form the proposal engine can use.

## Seed Cases

| Case | Dedupe Key | Sources | Prevention Status | Next Route |
| --- | --- | --- | --- | --- |
| BRIEF output drift | `brief-format-drift` | `COMPOUND-2026-06-09-001`, `COMPOUND-2026-06-10-002` | gate | keep response-contract and owner-doc gates current |
| Continuity pointer gap | `continuity-pointer-gap` | `COMPOUND-2026-06-10-003` | gate | keep `NEXT-SESSION-POINTER.yml` in taskset handoffs |
| Taskset completion inferred from claims | `taskset-completion-claim-only` | `COMPOUND-2026-06-10-004` | gate | use named taskset gate before completion claims |
| RSI operating evidence scattered | `rsi-evidence-scattered` | `REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration` | proposal | implement `TASKSET-AR-RSI-OPERATING-SYSTEM` |

## Rules

- A case with recurrence count greater than one cannot stay `note_only` without an accepted watch decision.
- A case with deterministic reproduction should gain a regression fixture or a task proposal.
- A case touching Owner-only boundaries must stay proposal-only until the Owner decision is explicit.

