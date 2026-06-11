# Diversity Council Protocol

## Purpose

The diversity council reviews high-impact planning changes through independent
operating lenses before a synthesis verdict is recorded.

## Viewpoints

- `skeptic`: looks for hidden failure modes and weak evidence.
- `advocate`: states the strongest case for the proposal.
- `explorer`: looks for adjacent opportunities and missed options.
- `stabilizer`: protects working invariants and rollback paths.
- `release-steward`: checks release, version, publish, PR, and Owner-gated boundaries.
- `evaluator`: checks eval, grader, verification, and regression evidence.
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
7. Verdict: `pass`, `watch`, `block`, or `no-action`.
8. Next action with owner boundary.

## Output Contract

Every council record must include:

- proposal id or planning rule id;
- participating viewpoints and structured role verdicts;
- minority concerns;
- unresolved assumptions;
- evidence references;
- verdict and score;
- next action.

Each role verdict must include `role`, `evidence_ref`, `decision`, `score`, and
`reason`. A block verdict must be resolved or explicitly converted to
`no-action` before the apply gate can run.

## Required Structured Verdicts

| Role | Required Check |
| --- | --- |
| `skeptic` | Weak evidence, hidden owner boundary, and false-positive risk. |
| `advocate` | Strongest case and expected value if accepted. |
| `stabilizer` | Rollback evidence, invariant protection, and blast radius. |
| `explorer` | Alternative lower-cost routes and missed adjacent evidence. |
| `release-steward` | Release/version/publish/PR boundary and Owner approval need. |
| `evaluator` | Verification command, eval regression risk, and fixture coverage. |

## Quantitative Metrics

Council synthesis records should link to evaluation records for
`proposal_precision`, `proposal_recall`, `eval_regression_rate`,
`repeated_failure_closure_rate`, and `false_positive_proposal_rate`.
