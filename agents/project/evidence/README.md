# Evidence Registry

## Purpose

This directory is the entrypoint for evidence that may drive planning proposals.
It keeps raw signals separate from canonical task, backlog, status, and release
mutations.

## Record Types

| Type | Directory | Use |
| --- | --- | --- |
| Inbox | `agents/project/evidence/inbox/` | Normalized trace, eval, grader, A2A, correction, review, retro, failure, compound, and conversation records before proposal scoring. |
| Evaluations | `agents/project/evidence/evaluations/` | Eval, grader, prediction-score, proposal quality, and regression metrics. |
| Verification | `agents/project/evidence/verification/` | Gate runs, commands, expected output, failure reasons, and closeout proof. |
| Casebooks | `agents/project/casebooks/` | Searchable failure and compound cases that should become fixtures, gates, or proposals. |

## Required Fields

| Field | Meaning |
| --- | --- |
| `evidence_id` | Stable identifier for dedupe and proposal references. |
| `source_type` | One of trace, eval, grader, A2A, correction, review, retro, failure, compound, conversation, gate, or owner_request. |
| `source_path` | Repo path or external pointer that produced the evidence. |
| `task_ref` | Related task or taskset when known. |
| `task_set_id` | Related task set such as `TASKSET-AR-RSI-OPERATING-SYSTEM` when known. |
| `dedupe_key` | Stable key used to merge repeated signals before proposal generation. |
| `observed_failure` | Specific reproduced failure, omission, drift, or gap when the signal is negative. |
| `observed_signal` | Concrete pass/watch/block signal when there is no failure. |
| `signal` | pass, watch, or block. |
| `owner_boundary` | Whether the evidence touches external, destructive, release, version, prod-data, cost-bearing, or Owner-only decisions. |
| `proposed_routing` | no_action, proposal, regression_fixture, owner_review, or archive. |
| `quality_check` | Dedupe, reproducibility, source freshness, and proposal precision checks required before task creation. |

## Rules

- Evidence is not a canonical mutation by itself.
- Proposal creation must dedupe records before adding work.
- Proposal creation must pass the `quality_check` before changing backlog, task, release, or skill state.
- Failed or rejected proposals stay useful as negative examples for precision metrics.
- Provider-live, remote, PR, tag, issue, or external evidence must be labeled separately from local deterministic gates.
