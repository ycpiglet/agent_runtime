---
id: TASK-AR-555
display_id: TASK-AR-555
task_uid: 64cd01b2-0e91-4d8d-96dd-b8cb9c9669a4
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-15T13:45:18+09:00
status: completed
resolution: done
priority: P3
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - release
  - automation
  - ops
started_at: 2026-06-15T13:45:18+09:00
completed_at: 2026-06-15T13:45:18+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-546-556.md
  - reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md
---

# TASK-AR-555 - End-to-end release automation (owner-gated)

## Goal

- Release stages are validated locally in `--check` mode only; remote tag/PR/merge/publish are manual. Add an owner-gated automation that, after approval, performs tag → PR → merge → publish with an audit trail.

## Scope

### Input
- `src/agent_runtime/publish_github_plan.py`, `publish_github_execute.py`, `release_preflight.py`, `release_cadence_trigger.py`.

### Process
- Add an owner-approval step that unlocks automatic remote execution; extend the cadence trigger with optional execution; keep signed commits + full audit.
- Default remains check-only; automation is explicit opt-in per release.

### Output
- An `--auto` path (owner-gated) through the existing publish tooling + audit records.

## Acceptance Criteria

- With owner approval, the pipeline performs tag/PR/merge/publish and records each step.
- Without approval, behavior is unchanged (check-only).
- All remote mutations are audited and reversible where possible.

## Evidence Targets

- Tooling diff + a dry-run transcript; release record.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` (release automation gap).
