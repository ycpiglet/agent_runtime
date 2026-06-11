# Failure and Compound Casebook

## Purpose

This casebook is the query surface for repeated failures and compound issues.
It does not replace `agents/lead_engineer/compound_log.md`; it indexes entries
into a form the proposal engine can use.

## Seed Cases

| Case | Dedupe Key | Symptom | Trigger | Owner Boundary | Affected Gate | Recurrence Count | Linked Regression Fixture | Prevention Status | Needs Enforcement | Next Route |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| BRIEF output drift | `brief-format-drift` | Owner-facing report collapses required BRIEF frame. | backlog/status/report request | local | `owner_doc_format_gate.py` | 2 | owner-doc format fixture | gate | no | keep response-contract and owner-doc gates current |
| Continuity pointer gap | `continuity-pointer-gap` | Handoff omits active taskset or stale pointer survives. | session closeout / resume | local | `continuity_contract_gate.py` where present | 1 | not_yet | gate | no | keep `NEXT-SESSION-POINTER.yml` in taskset handoffs |
| Taskset completion inferred from claims | `taskset-completion-claim-only` | Claim text implies completion without named gate evidence. | taskset closeout | local | `taskset_work_gate.py --require-complete` | 1 | taskset gate | gate | no | use named taskset gate before completion claims |
| RSI operating evidence scattered | `rsi-evidence-scattered` | Trace, eval, review, retro, failure, and Owner conversation evidence are split across surfaces. | RSI OS registration review | local | `verify_rsi_operating_system_taskset.py` | 1 | `tests/test_rsi_operating_system_docs.py` | proposal | yes | complete `TASKSET-AR-RSI-OPERATING-SYSTEM` |

## Rules

- A case with recurrence count greater than one cannot stay `note_only` without an accepted watch decision.
- A case with deterministic reproduction should gain a regression fixture or a task proposal.
- A case touching Owner-only boundaries must stay proposal-only until the Owner decision is explicit.
- A `needs_enforcement` case must name a task proposal, gate, fixture, or
  accepted_watch reason before closeout.
- `agents/lead_engineer/compound_log.md` remains the historical source; this
  casebook is the current query surface for RSI proposal routing.

