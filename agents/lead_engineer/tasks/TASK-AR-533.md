---
id: TASK-AR-533
display_id: TASK-AR-533
task_uid: 4e786186-f46e-4642-b817-16c0f14943f3
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
started_at: 2026-06-14T09:00:00+09:00
updated_at: 2026-06-14T09:20:14+09:00
completed_at: 2026-06-14T09:20:14+09:00
status: completed
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - backlog-board
  - attention-surface
---

# TASK-AR-533 - Board attention-lanes + archive manifest extraction

## Goal

- Turn `BACKLOG-BOARD.md` from a data dump (currently ~69% inline "Archived Task Files") back into an *attention surface*: Triage / Active / Rollup lanes, with archive moved to a separate generated index referenced by count + link. (Overview-first; progressive disclosure.)

## Scope

- Modify `scripts/backlog_board.py` to render three lanes: Triage (new/unclassified), Active working set (in-progress/this-iteration, full detail), Rollups (counts + pointers for backlog/done/archived — never inline).
- Emit a generated `ARCHIVE-INDEX.md` (id + title + 1-line + link per archived item); board shows only the archived **count + pointer**.
- Keep the board generated/idempotent; state-sync gate stays green.

## Acceptance Criteria

- Board no longer inlines archived task files; archived items live in `ARCHIVE-INDEX.md`.
- Active lane shows only open work in full; rollups show counts + links.
- `python scripts/backlog_board.py --write` regenerates both deterministically.

## Dependency / Footprint

- depends_on: none (foundational).
- target_files: `scripts/backlog_board.py`, `BACKLOG-BOARD.md`, `ARCHIVE-INDEX.md` (new). Disjoint from 534/535/536. NOT disjoint from 538 (both edit backlog_board.py) -> different wave.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (Linear Triage/Inbox, Jira backlog-vs-board, GitHub Projects views, Shneiderman overview-first).

## Completion Evidence

- `scripts/backlog_board.py`: added `render_archive_index()`, replaced the inline `## Archived Task Files` table with a `## Rollups` section (count + pointer), `main()` now also writes `ARCHIVE-INDEX.md`.
- `tests/test_backlog_board_tasksets.py`: contract updated — board has no `## Archived Task Files`, has `## Rollups` pointing to `ARCHIVE-INDEX.md`, completed IDs absent from board; `render_archive_index` carries the per-file detail.
- Result: `BACKLOG-BOARD.md` 346 -> 183 lines; all 182 completed task files preserved in `ARCHIVE-INDEX.md` (byte-identical ID set, zero loss).

## Verification Results

- W4a: `pytest tests/test_backlog_board_tasksets.py` 8 passed; full suite exit 0; `owner_governance_gate.py` exit 0; output byte-stable across two `--write` runs.
- W4b (independent, verifier != worker): APPROVE — `reviews/W4B-2026-06-14-TASK-AR-533.md`. All 5 criteria PASS (no data loss, board de-dumped, idempotent, gates green, active board intact).
