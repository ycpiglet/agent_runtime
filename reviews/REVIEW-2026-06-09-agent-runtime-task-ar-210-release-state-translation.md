# REVIEW: TASK-AR-210 Release-State Translation

## Bottom Line

`ready_for_governance_review` from `TASK-AR-223` is translated to the allowed release state `hold_for_data`.

## Decision

- release_state: `hold_for_data`
- release_cause: `migration_or_dataset_evidence_gap`
- decision_deadline: `2026-07-02`
- owner: `lead-engineer`
- blocked_by:
  - `TASK-AR-220`
  - `TASK-AR-215`
  - `TASK-AR-204`
- impact_on_version: `v0.1.8` can keep baseline validation evidence, but cannot be marked `ready` or `release` until migration approval closure, overlay simulation, and co-location enforcement boundaries are closed or explicitly owner-approved.

## Why Not Ready

- `agents/project/MIGRATION-HOLD-ROUTING.yml` explicitly declares `release_state: hold_for_data`.
- `scripts-source-only` still contains 53 source-only items routed through hold handling.
- `TASK-AR-215` overlay simulation remains `in_progress`, so `hold_for_overlay` remains a secondary boundary.
- `TASK-AR-204` co-location block enforcement is still a governance boundary.

## Evidence Accepted

- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md`
- `reviews/OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json`
- `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json`
- `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json`
- `reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json`
- `agents/project/MIGRATION-HOLD-ROUTING.yml`
- `agents/project/MIGRATION-COMPAT-MAP.yml`
- `agents/lead_engineer/tasks/TASK-AR-215.md`

## Secondary Routes

- `hold_for_overlay`: applies if cross-project overlay simulation is still incomplete at the decision window.
- `block`: applies if any hold route is converted to warn-only or lacks required owner/approved_by/decision_date/expiry/justification where required.

## Next Action

Move to `TASK-AR-222` closeout bundle completion with this release-state decision. Then continue `TASK-AR-220` migration approval closure, `TASK-AR-215` overlay simulation, and `TASK-AR-204` co-location enforcement.

## Verification

- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-release-state --check`
- Result: `findings=0`
