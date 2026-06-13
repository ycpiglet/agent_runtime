---
id: TASK-AR-538
display_id: TASK-AR-538
task_uid: 42d85997-bac8-4afb-b10b-664356a235de
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P2
difficulty: S
est_hours: 4
est_tokens: 3500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - triage
  - state-machine
---

# TASK-AR-538 - Triage/intake status + needs-attention lane

## Goal

- Add an explicit intake state so new items wait in a triage inbox (excluded from the active working set) until accepted/deferred — the Linear Triage model — as a status FIELD, not a directory move.

## Scope

- Add `status: triage` to the status vocabulary: items in triage are excluded from the Active lane and surfaced in the Triage lane (TASK-AR-533) with an accept (-> backlog/planned) / defer (-> someday) transition.
- Render the Triage lane + a "needs attention" rollup (stale claims, unaccepted intake, items missing owner) on the board.
- Coordinate with the host-feedback intake queue (TASK-AR-526) so host feedback enters via `triage`.

## Acceptance Criteria

- `status: triage` items appear only in the Triage lane, not Active; accept/defer transitions are documented.
- A "needs attention" rollup surfaces exception items (not the full store).
- Host-feedback intake (TASK-AR-526) routes through the triage state.

## Dependency / Footprint

- depends_on: TASK-AR-533 (board lanes), TASK-AR-526 (intake queue).
- target_files: `scripts/backlog_board.py` (status handling), status enum docs. OVERLAPS TASK-AR-533 (same file) -> must run in a later wave, not parallel.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (Linear Triage excluded-from-views intake; Datadog Monitor Quality "needs attention"; GTD Next-Actions vs Someday/Maybe).
