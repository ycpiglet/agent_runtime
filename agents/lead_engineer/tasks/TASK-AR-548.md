---
id: TASK-AR-548
display_id: TASK-AR-548
task_uid: 26100de0-a450-4e8f-8db2-aed073180b22
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - forms
  - ux
  - validation
---

# TASK-AR-548 - Form validation + error UX (inline, toast, undo)

## Goal

- Form errors currently surface in a single global list and a failed submit can reset the form; there is no undo for destructive actions. Add per-field inline validation, toast notifications, and an undo affordance.

## Scope

### Input
- `src/agent_runtime/ui_console.py` forms + `ui_commands.py` validation contracts.
- Verification cases VC-UIF-2/3/4/6.

### Process
- Bind validation errors to fields via `aria-describedby`; preserve user input on failed submit.
- Add transient toast for success/error; add an undo stack for destructive/bulk actions.

### Output
- Inline validation + toast + undo in the console; respects proposal-only command boundary.

## Acceptance Criteria

- A failed submit shows the error next to the offending field and preserves input.
- Success/error toasts appear and auto-dismiss; screen-reader announced.
- Destructive actions are undoable for a short window.

## Evidence Targets

- Console diff + UI tests (and e2e from TASK-AR-546) for VC-UIF cases.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`.
