# Evidence-to-Proposal Contract

## Purpose

This contract defines how normalized evidence becomes a proposal without direct
canonical mutation. It extends the planning loop by making evidence source,
dedupe, risk, owner boundary, council review, and verification requirements
machine-checkable before any task, plan, doc, eval, release, or skill work is
created.

## Inputs

| Source | Required Fields | Route |
| --- | --- | --- |
| Evidence inbox | `source_type`, `source_path`, `task_ref`, `task_set_id`, `dedupe_key`, `quality_check` | proposal or no action |
| Evaluation registry | `record_id`, `source_command`, `source_path`, `scope_boundary`, metric fields | proposal metric input |
| Verification registry | `record_id`, `command`, `result`, `findings`, `scope_boundary` | closeout and apply verifier |
| Casebook | `case_id`, `dedupe_key`, `symptom`, `trigger`, `owner_boundary`, `prevention_status` | regression or follow-up proposal |
| A2A lifecycle | `context_id`, `task_id`, `request`, `review`, `decision`, `correction`, `proposal_routing` | planning evidence |

## Proposal Record Requirements

Every proposal record must include:

- `id`
- `mode`
- `status`
- `proposal_output`
- `action_type`
- `risk_tier`
- `title`
- `dedupe_key`
- `evidence_hash`
- `source_refs`
- `evidence`
- `affected_owner_boundary`
- `owner_boundary`
- `expected_verification_command`
- `verifier_list`
- `target_files`
- `blast_radius`
- `rollback_path`
- `rejection_reason`

## Outputs

| Output | Meaning |
| --- | --- |
| `task` | Draft task or worker-ready unit proposal. |
| `plan` | Plan, roadmap, or taskset decomposition update. |
| `doc` | Documentation or owner-facing record repair. |
| `eval` | Evaluation, grader, fixture, or verification expansion. |
| `release` | Release/version consistency proposal. |
| `skill` | Skill packaging or routing contract proposal. |
| `no_action` | Evidence was useful but should not create work. |

Rejected and `no_action` proposals remain durable negative examples for
proposal precision tracking. They must preserve `rejection_reason`, evidence
refs, and dedupe key.

## Quality Scoring

| Metric | Required Source | Notes |
| --- | --- | --- |
| `proposal_precision` | accepted, rejected, and no-action proposal counts | Accepted useful proposals divided by all generated proposals. |
| `proposal_recall` | known actionable failures and accepted proposals | Known actionable failures that received adequate proposals. |
| `false_positive_proposal_rate` | rejected/no-action proposals | Higher rate blocks C-mode. |
| `eval_regression_rate` | evaluation registry | Regression count divided by recently passing evals in the same area. |
| `repeated_failure_closure_rate` | casebook | Repeated failures with fixture, gate, task, or accepted watch. |

## Apply Boundary

- Default mode is B-mode proposal-only.
- No proposal engine path may write `BACKLOG.md`, `BACKLOG-BOARD.md`,
  `STATUS.md`, task files, release files, or owner docs without the apply gate.
- Owner-only, external, destructive, release/version, dependency, secret,
  production-data, cost-bearing, and gate-weakening changes remain Owner-gated.
- Apply requires a passing verifier list, rollback path, risk tier, blast radius,
  and council verdict for high-impact proposals.

