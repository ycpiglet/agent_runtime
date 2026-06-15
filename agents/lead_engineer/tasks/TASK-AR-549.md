---
id: TASK-AR-549
display_id: TASK-AR-549
task_uid: acc358de-d053-4f34-9569-280f5e512763
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-15T13:45:18+09:00
status: completed
resolution: done
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - accessibility
  - a11y
  - wcag
started_at: 2026-06-15T13:45:18+09:00
completed_at: 2026-06-15T13:45:18+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-546-556.md
  - reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md
---

# TASK-AR-549 - Accessibility uplift (skip links, focus, semantics, contrast)

## Goal

- The console has broad ARIA usage but misses several WCAG essentials. Add skip-to-content, modal focus management, table semantics for list data, proper label association, and a token contrast audit, plus an automated a11y scan.

## Scope

### Input
- `src/agent_runtime/ui_console.py` shell, modals, lists, CSS tokens.
- Verification cases VC-UIA-2/3/4/5.

### Process
- Add a visible skip link; trap+restore focus in modals (experience settings, workspace switcher).
- Render evidence/state lists as real `<table>` with header scope; associate `<label for>`; document/verify token contrast >= WCAG AA.
- Add an axe-core scan (via the Playwright suite from TASK-AR-546).

### Output
- a11y fixes in the console + an automated axe scan in CI.

## Acceptance Criteria

- Skip link works; modals trap and restore focus.
- Tabular data uses semantic tables; inputs have associated labels.
- axe-core scan passes with zero serious/critical violations on core views.

## Evidence Targets

- Console diff + axe-core report; VC-UIA cases.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`.
