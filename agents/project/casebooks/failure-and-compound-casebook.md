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
| RSI operating evidence scattered | `rsi-evidence-scattered` | `REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration` | verified | `TASKSET-AR-RSI-OPERATING-SYSTEM` closeout |
| Low-frequency self-improvement debt | `self-improvement-low-frequency-debt` | `reviews/REVIEW-2026-06-17-self-improvement-cycle.md`, `COMPOUND-2026-06-17-001` | watch | route dormant roles and low-reuse assets into the next cycle |

## Detailed Cases

### CASE-BRIEF-FORMAT-DRIFT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-BRIEF-FORMAT-DRIFT` |
| `dedupe_key` | `brief-format-drift` |
| `symptom` | Owner-facing backlog/report output collapses into an unstructured task list. |
| `trigger` | User asks for backlog, plan, report, or status. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/owner_doc_format_gate.py`, response contract checks |
| `recurrence_count` | 2+ |
| `source_refs` | `agents/lead_engineer/compound_log.md`, `reviews/REVIEW-2026-06-09-backlog-brief-format-drift-compound.md` |
| `reproduction` | Run owner-doc format gate against listed owner docs. |
| `linked_regression_fixture` | `tests/test_backlog_board_tasksets.py` and owner-doc gate manifest |
| `task_proposal` | completed governance/board follow-up |
| `prevention_status` | gate |

### CASE-CONTINUITY-POINTER-GAP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CONTINUITY-POINTER-GAP` |
| `dedupe_key` | `continuity-pointer-gap` |
| `symptom` | Resume state becomes ambiguous across panes and tasksets. |
| `trigger` | Session closeout or taskset handoff. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/continuity_contract_gate.py`, `scripts/taskset_work_gate.py` |
| `recurrence_count` | 1+ |
| `source_refs` | `COMPOUND-2026-06-10-003`, `agents/project/NEXT-SESSION-POINTER.yml` |
| `reproduction` | Run continuity gate after pointer or claim changes. |
| `linked_regression_fixture` | continuity gate tests and taskset gate |
| `task_proposal` | completed continuity/session-closeout automation |
| `prevention_status` | gate |

### CASE-TASKSET-COMPLETION-CLAIM-ONLY

| Field | Value |
| --- | --- |
| `case_id` | `CASE-TASKSET-COMPLETION-CLAIM-ONLY` |
| `dedupe_key` | `taskset-completion-claim-only` |
| `symptom` | A taskset is claimed complete while one or more canonical task files remain planned/open. |
| `trigger` | Claim release or closeout report. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/taskset_work_gate.py --require-complete` |
| `recurrence_count` | 2+ |
| `source_refs` | `COMPOUND-2026-06-10-004`, `TASKSET-AR-VISION-GAP-CLOSURE`, `TASKSET-AR-RSI-OPERATING-SYSTEM` |
| `reproduction` | Run named taskset gate with `--require-complete`. |
| `linked_regression_fixture` | `tests/test_taskset_work_gate.py` |
| `task_proposal` | no new proposal; closeout gate is now required |
| `prevention_status` | gate |

### CASE-RSI-EVIDENCE-SCATTERED

| Field | Value |
| --- | --- |
| `case_id` | `CASE-RSI-EVIDENCE-SCATTERED` |
| `dedupe_key` | `rsi-evidence-scattered` |
| `symptom` | Trace, eval, A2A, correction, review, and retro evidence cannot reliably become proposals. |
| `trigger` | RSI operating-system registration and follow-up closeout. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/verify_rsi_operating_system_taskset.py` |
| `recurrence_count` | 1 |
| `source_refs` | `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md` |
| `reproduction` | Run RSI verification wrapper and inspect evidence registries. |
| `linked_regression_fixture` | `tests/test_rsi_operating_system_docs.py`, `tests/test_a2a_lifecycle_gate.py` |
| `task_proposal` | `TASK-AR-297` through `TASK-AR-305` |
| `prevention_status` | verified |

## Rules

- A case with recurrence count greater than one cannot stay `note_only` without an accepted watch decision.
- A case with deterministic reproduction should gain a regression fixture or a task proposal.
- A case touching Owner-only boundaries must stay proposal-only until the Owner decision is explicit.
- `needs enforcement` entries must route to a task proposal or an explicit `accepted_watch` decision before closeout.

### CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT` |
| `dedupe_key` | `self-improvement-low-frequency-debt` |
| `symptom` | Low-frequency roles and runtime assets stay visible as watch debt. |
| `trigger` | `scripts/self_improvement_cycle.py assess` reports immature/watch. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/collaboration_governance_gate.py`, `scripts/runtime_asset_usage.py` |
| `recurrence_count` | role gaps `6`; asset gaps `17` |
| `source_refs` | `reviews/REVIEW-2026-06-17-self-improvement-cycle.md`, `COMPOUND-2026-06-17-001` |
| `reproduction` | Run `python scripts/self_improvement_cycle.py assess --json`. |
| `linked_regression_fixture` | `tests/test_self_improvement_cycle.py` |
| `task_proposal` | `TASK-AR-571`, then `TASK-AR-572` maturity reporting |
| `prevention_status` | watch |
