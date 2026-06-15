---
id: TASK-AR-547
display_id: TASK-AR-547
task_uid: 333e7d79-d97a-453d-a50d-f5fed62e43cd
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-15T13:45:18+09:00
status: completed
resolution: done
priority: P2
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - responsive
  - css
  - mobile
started_at: 2026-06-15T13:45:18+09:00
completed_at: 2026-06-15T13:45:18+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-546-556.md
  - reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md
---

# TASK-AR-547 - Responsive layout for tablet/phone

## Goal

- The console is single-column with fixed widths and a fixed sidebar; it breaks below desktop widths. Add responsive layout so tablet (768px) and phone (375px) are usable.

## Scope

### Input
- `src/agent_runtime/ui_console.py` shell + CSS token system.
- Verification cases VC-UIR-1/2/3.

### Process
- Add a viewport meta + CSS media queries: tablet collapses the sidebar to a hamburger drawer; phone goes full-width with stacked panels.
- Ensure touch targets >= 44px; avoid horizontal-scroll traps in narrow columns.

### Output
- Responsive CSS in the console template; documented breakpoints.

## Acceptance Criteria

- At 768px the sidebar collapses to a toggleable drawer; at 375px panels stack without overflow.
- No horizontal scroll trap; long content wraps/truncates.
- Existing desktop layout and tests unchanged.

## Evidence Targets

- Console CSS diff + (with TASK-AR-546) Playwright viewport snapshots at 375/768/1280.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`.
