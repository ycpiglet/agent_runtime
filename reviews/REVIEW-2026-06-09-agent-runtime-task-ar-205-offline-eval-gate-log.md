# REVIEW: TASK-AR-205 Offline Eval Gate Log

## Bottom Line

The offline eval lane is now executable, but it blocks release readiness. Current committed goldsets are too small and under-specified to satisfy the 90% gate.

## Signal

- Added evaluator: `scripts/offline_eval_gate.py`.
- Policy source: `agents/project/EVAL-POLICY.yml`.
- Dataset source: `agents/project/DATASET-CATALOG.yml`.
- Output report: `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json`.
- Command: `python scripts/offline_eval_gate.py --out reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json`.
- Result: `status=block`.
- Syntax check: `python -m py_compile scripts/offline_eval_gate.py` passed.
- Re-run output: `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-rerun.json`.
- Re-run result: `status=block` with the same two dataset scores.

## Dataset Results

- `project-overlay-routing-gold`: `score=0.6667`, `cases=2`, `findings=4`.
- `project-metadata-gov-gold`: `score=0.6667`, `cases=2`, `findings=4`.

## Insight

- The gate should not pass from aggregate existence of JSONL files.
- Required case types from policy are not covered.
- Dataset rows need `case_type`, `source_refs`, and `query_contract` metadata so correctness can be interpreted by domain, ambiguity, access, and tradeoff.
- Current result is a useful release blocker, not a failed implementation.

## Decision

- Route this lane to `hold_for_data`.
- Do not mark `TASK-AR-217` release rehearsal ready until offline eval reaches at least `0.90` by dataset/domain or has an explicit owner-approved waiver.
- Next data work: expand both goldsets with typical, edge, adversarial, ambiguous, and access-controlled cases.
