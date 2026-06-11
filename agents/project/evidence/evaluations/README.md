# Evaluation Evidence Registry

## Purpose

This registry makes eval, grader, prediction-score, proposal-quality, and
regression records queryable for the RSI operating system.

## Seed Evidence

| Evidence | Current Source |
| --- | --- |
| RSI planning verification | `reviews/RSI-PLANNING-TASKSET-VERIFY.json` |
| Planning evidence link | `reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json` |
| Offline eval reports | `reviews/OFFLINE-EVAL-*.json` |
| Prediction score reports | `reviews/OFFLINE-PREDICTION-SCORE-*.json` |
| Live reviewer gates | `reviews/LIVE-REVIEWER-GATE-*.json` |

## Evaluation Record Shape

| Field | Meaning |
| --- | --- |
| `record_id` | Stable identifier for query, dedupe, and proposal references. |
| `source_type` | eval, grader, prediction_score, proposal_quality, regression, or live_reviewer. |
| `source_command` | Exact command or tool invocation that produced the record, or `none` for imported reports. |
| `source_path` | JSON, markdown, fixture, or report path that stores the source evidence. |
| `task_ref` | Related task, taskset, release, proposal, or `none`. |
| `scope_boundary` | `local_deterministic`, `template_local`, `provider_live`, `remote_ci`, `release`, or `external`. |
| `result` | pass, watch, block, regression, or no_action. |
| `metric_name` | Metric populated by the record, such as `proposal_precision`. |
| `metric_value` | Numeric score, ratio, count, or `n/a` if the record is qualitative. |

## Required Metrics

| Metric | Meaning |
| --- | --- |
| `proposal_precision` | Accepted useful proposals divided by all proposals generated for a window. |
| `proposal_recall` | Known actionable failures that received an adequate proposal. |
| `eval_regression_rate` | Passing eval cases that later fail in the same area. |
| `repeated_failure_closure_rate` | Repeated failures that gained a fixture, gate, or accepted task. |
| `evidence_to_task_latency` | Time from evidence record to accepted task or explicit no-action decision. |

## How To Add

1. Store the raw report under `reviews/` or an evidence subdirectory before summarizing it.
2. Add a normalized record with `record_id`, `source_command`, `source_path`, `task_ref`, `scope_boundary`, and metric fields.
3. Mark local deterministic evidence as `local_deterministic` and live service evidence as `provider_live`; never use a local pass as provider-live proof.
4. Link the record to a proposal only after dedupe and quality checks pass.

## Boundary

Local deterministic evals and provider-live evals must be stored as different
evidence classes. Local pass does not imply provider-live pass. Future proposal
scoring should consume these records directly instead of free-form review scraping.
