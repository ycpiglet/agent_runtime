# Evidence-to-Proposal Contract

## Purpose

This contract defines how RSI operating-system evidence becomes bounded
proposal output. It consumes the evidence inbox, evaluation registry,
verification registry, and failure casebook, then writes proposal records only.
The apply gate is the only path from proposal to canonical mutation.

## Inputs

| Input | Required Fields | Boundary |
| --- | --- | --- |
| Evidence inbox | `record_id`, `source_type`, `source_path`, `task_ref`, `task_set_id`, `dedupe_key`, `owner_boundary`, `quality_check` | Normalized evidence only. |
| Evaluation registry | `record_id`, `source_command`, `metric_name`, `metric_value`, `scope_boundary` | Distinguish local deterministic and provider-live evidence. |
| Verification registry | `record_id`, `source_command`, `expected_output`, `result`, `failure_reason` | Commands must be reproducible or marked non-repro. |
| Casebook | `case_id`, `dedupe_key`, `symptom`, `trigger`, `affected_gate`, `linked_regression_fixture` | Repeated failures route to fixture, gate, task proposal, or accepted watch. |

## Proposal Record

Every proposal record must include:

| Field | Meaning |
| --- | --- |
| `evidence_ids` | Normalized evidence or trace IDs used to justify the proposal. |
| `dedupe_key` | Stable key that collapses repeated evidence into one proposal lineage. |
| `affected_owner_boundary` | Local, Owner-only, external, destructive, release, version, prod-data, or cost-bearing boundary. |
| `expected_verification_command` | First command that must pass before the proposal can be closed or applied. |
| `risk_tier` | low, medium, high, or owner. |
| `estimated_blast_radius` | single_file, multi_file, or owner_gated. |
| `failure_regression_links` | Casebook, trace, eval, or fixture IDs that would regress if ignored. |
| `proposal_output` | One of task, plan, doc, eval, release, skill, or no_action. |
| `rejection_reason` | Required when council review or quality scoring rejects the proposal. |

## Output Types

| `proposal_output` | Canonical Target | Apply Boundary |
| --- | --- | --- |
| `task` | `agents/lead_engineer/tasks/` | Apply gate plus task identity and board regeneration. |
| `plan` | `docs/superpowers/plans/` or project planning docs | Apply gate; no release/version mutation. |
| `doc` | Owner or project docs | Apply gate; owner-doc format gate when Owner-facing. |
| `eval` | eval, grader, fixture, or verification records | Local deterministic first. |
| `release` | release/version steward proposal | Owner-gated; never auto-applied. |
| `skill` | `skills/*/SKILL.md` | Must route to concise local skill docs and gates. |
| `no_action` | Negative example | Preserved for proposal_precision and false_positive_proposal_rate. |

## Quality Gate

- Weak evidence below the planning-loop confidence floor becomes `no_action` or
  `watch`, not a task.
- Rejected proposals remain queryable negative examples for precision tracking.
- Proposal quality metrics include `proposal_precision`, `proposal_recall`,
  `eval_regression_rate`, `repeated_failure_closure_rate`, and
  `false_positive_proposal_rate`.
- A proposal with an unresolved council block verdict cannot enter apply-gate
  execution.

## Apply Gate

The proposal engine does not write canonical backlog, status, task, release,
or owner-doc files directly. Canonical mutation requires:

1. proposal status `approved`;
2. no unresolved council block verdict;
3. verifier list and rollback path;
4. Owner approval for high, owner, release, version, external, destructive,
   prod-data, cost-bearing, or PR/publish actions;
5. post-apply verification evidence recorded in the verification registry.
