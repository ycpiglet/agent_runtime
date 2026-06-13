---
id: TASK-AR-533
display_id: TASK-AR-533
task_uid: 4e786186-f46e-4642-b817-16c0f14943f3
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
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
