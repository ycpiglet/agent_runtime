# REVIEW: TASK-AR-207 Correction Collector Log

## Bottom Line

The correction collector lane is executable and passes. Failed eval/reviewer reports now generate owner-routed correction proposal files.

## Signal

- Added collector: `scripts/correction_collector.py`.
- Added reviewer failure sample: `agents/project/live_review/live-review-failure-sample-2026-06-09.jsonl`.
- Failure sample gate report: `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample.json`.
- Collector summary: `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json`.
- Syntax check: `python -m py_compile scripts/correction_collector.py` passed.

## Execution

- Live reviewer failure sample result: `status=block`, `score=0.7059`, `findings=5`.
- Correction collector result: `status=pass`, `written=2`.
- Re-run result: `status=pass`, `written=2`.
- Release bundle check after adding collector/evidence: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-correction --check`, result `findings=0`.

## Generated Proposals

- `agents/project/corrections/2026-06-09-offline-eval-2026-06-09-task-ar-217-1-goldset-metadata-completion.md`
- `agents/project/corrections/2026-06-09-live-reviewer-gate-2026-06-09-task-ar-207-failure-sample-1-reviewer-footer-failure.md`

## Boundary

Collector output is proposal-only. It must not modify source-of-truth definitions without owner/accountable human approval.

## Decision

Move `TASK-AR-217` from correction collector lane to `TASK-AR-208` A2A trace reconstruction.
