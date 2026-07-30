# TASK-AR-654 W4 evidence footprint amendment

- Date: 2026-07-30
- Task: `TASK-AR-654`
- Unit: `UNIT-TASK-AR-654-001`
- Claim: `CLAIM-20260730-092200-task-ar-654-host-gates`
- Decision: approved as a lifecycle-only footprint amendment

## Reason

W4 verification and independent review produce deterministic repository evidence
outside the original implementation footprint. Claim release also updates the
claim record and appends the standard pane-event and A2A projections. Those
paths are part of the same governed unit closeout and must be declared before
the enforced post-verification footprint check runs.

## Added footprint

- The unit record and the three claim lifecycle records.
- `reviews/INDEX.md`, the unit's W4a evidence glob, and its W4b review glob.
- This amendment record.
- The standard claim-release pane-event and A2A append-only projections.
- The task registration, planning snapshot, owner-manifest, backlog, and
  runtime-instance projections already committed as part of TASK-AR-654 before
  its implementation worktree branched.

No implementation scope, acceptance criterion, product behavior, or protected
TASK-AR-648 surface changed.
