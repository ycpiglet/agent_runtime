# Evidence Inbox

## Purpose

The inbox is the landing zone for normalized evidence before the proposal engine
decides whether to create work.

## Intake Contract

| Field | Required | Notes |
| --- | --- | --- |
| `source_type` | yes | trace, eval, grader, A2A, correction, review, retro, failure, compound, conversation, or owner_request. |
| `source_path` | yes | Path to the raw evidence, review, report, or fixture. |
| `task_ref` | yes | Related task, task file, or `none` when not yet linked. |
| `task_set_id` | yes | Related task set, usually `TASKSET-AR-RSI-OPERATING-SYSTEM` for this registry. |
| `dedupe_key` | yes | Stable key such as `brief-format-drift` or `a2a-lifecycle-missing-decision`. |
| `summary` | yes | One sentence describing the signal. |
| `observed_failure` | conditional | Required for block/watch failure evidence; use `none` for positive evidence. |
| `observed_signal` | yes | Concrete observed pass, watch, block, drift, omission, or regression signal. |
| `signal` | yes | pass, watch, or block. |
| `candidate_action` | yes | no_action, task_proposal, doc_proposal, eval_proposal, skill_proposal, release_proposal, or regression_fixture. |
| `proposed_routing` | yes | no_action, proposal, regression_fixture, owner_review, council_review, or archive. |
| `owner_boundary` | yes | local, owner_review, external, destructive, release, version, prod_data, or cost_bearing. |
| `quality_check` | yes | Must describe dedupe status, source freshness, reproducibility, and proposal precision/recall expectation. |

## Routing

- `block` evidence with a reproduction path should route to the casebook and a regression fixture proposal.
- `watch` evidence with repeated recurrence should route to council review before task creation.
- Conversation evidence should preserve the Owner decision and constraints, then route through the proposal engine.
- A2A lifecycle evidence must include context ID, task ID, request, review, decision, correction, and reconstruction result before it is considered verified.
- Local A2A lifecycle evidence is verified with `python scripts/a2a_lifecycle_gate.py --json --write-record`; provider-live transport remains out of scope until deterministic fixtures pass.
- Inbox records route to proposal generation only after `dedupe_key` and `quality_check` are reviewed.
