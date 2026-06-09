# REVIEW: TASK-AR-205 Goldset Expansion Log

## Bottom Line

The goldset readiness blocker is resolved. Both committed datasets now cover required case types and include `source_refs` plus `query_contract` metadata.

## Signal

- Updated `agents/project/evals/overlay-routing-v1.jsonl`.
- Updated `agents/project/evals/gov-metadata-v1.jsonl`.
- Each dataset now has 5 cases.
- Required case types covered: `typical`, `edge`, `adversarial`, `ambiguous`, `access-controlled`.
- Every row has `source_refs`.
- Every row has `query_contract`.

## Gate Result

- Command: `python scripts/offline_eval_gate.py --out reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json`.
- Result: `status=pass`.
- `project-overlay-routing-gold`: `score=1.0`, `cases=5`, `findings=0`.
- `project-metadata-gov-gold`: `score=1.0`, `cases=5`, `findings=0`.
- Release bundle check after adding `scripts/offline_eval_gate.py`: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-goldset --check`, result `findings=0`.

## Boundary

This is a goldset readiness pass, not a model-output accuracy pass. The report explicitly records `accuracy_claim=not_model_output_accuracy`.

## Decision

Move `TASK-AR-205` from data-shape blocker to prediction-scoring blocker. The next offline eval step is to score actual agent/model outputs against these goldsets.
