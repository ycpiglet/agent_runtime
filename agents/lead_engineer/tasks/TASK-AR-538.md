---
id: TASK-AR-538
display_id: TASK-AR-538
task_uid: 42d85997-bac8-4afb-b10b-664356a235de
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
started_at: 2026-06-14T11:45:00+09:00
updated_at: 2026-06-14T12:00:00+09:00
completed_at: 2026-06-14T12:00:00+09:00
status: completed
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

## Completion Evidence

- `scripts/backlog_board.py`: `TRIAGE_STATUSES = {triage, intake}` + `is_triage()`; `open_tasks` now excludes triage (held out of active lanes); a `## Triage` inbox section renders triage items with the accept(-> planned)/defer hint; a `## Rollups` `Needs attention` line counts `triage + Ask-lane`.
- `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`: documents the triage intake state + accept/defer transitions; consistent with `HOST-FEEDBACK-QUEUE.json` (triage -> accepted/deferred/rejected, TASK-AR-526). Status FIELD + view, not a directory move.
- `tests/test_backlog_board_tasksets.py`: triage task held out of active + shown in Triage; needs-attention rollup present.

## Verification Results

- W4a: 9 board tests pass; board regenerates ("Needs attention" line; no empty Triage section when 0 triage); governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-538.md`.
