# Diversity Council Protocol

## Purpose

The diversity council reviews high-impact planning changes through independent
operating lenses before a synthesis verdict is recorded.

## Viewpoints

- `skeptic`: looks for hidden failure modes and weak evidence.
- `advocate`: states the strongest case for the proposal.
- `explorer`: looks for adjacent opportunities and missed options.
- `stabilizer`: protects working invariants and rollback paths.
- `pragmatist`: checks cost, sequence, and operator burden.
- `systems-thinker`: checks feedback loops and second-order effects.
- `user-impact-reviewer`: checks Owner/user experience and decision clarity.
- `evidence-librarian`: verifies source references and traceability.

## Debate Flow

1. Independent notes.
2. Premortem.
3. Advocate case.
4. Skeptic case.
5. Evidence check.
6. Synthesis.
7. Verdict: `pass`, `watch`, `block`, or `no_action`.
8. Next action with owner boundary.

## Output Contract

Every council record must include:

- proposal id or planning rule id;
- participating viewpoints;
- minority concerns;
- unresolved assumptions;
- evidence references;
- verdict and score;
- next action.

## Verdict Fields

Every structured council verdict must include:

| Field | Meaning |
| --- | --- |
| `proposal_id` | Proposal or planning rule under review. |
| `role` | `skeptic`, `advocate`, `stabilizer`, `explorer`, `release-steward`, or `evaluator`. |
| `evidence_ref` | Evidence inbox, casebook, eval, verification, or A2A lifecycle record. |
| `decision` | `pass`, `watch`, `block`, or `no_action`. |
| `score` | Numeric score from 0 to 100. |
| `reason` | Short reason grounded in evidence. |
| `owner_boundary` | local, owner_review, external, destructive, release, version, prod_data, or cost_bearing. |

## Proposal Metrics

Council outcomes contribute to:

- `proposal_precision`
- `proposal_recall`
- `eval_regression_rate`
- `repeated_failure_closure_rate`
- `false_positive_proposal_rate`

Metrics are computed over accepted, rejected, deferred, blocked, superseded, and
`no_action` proposals. A proposal with any unresolved `block` verdict cannot
enter apply-gate execution.
