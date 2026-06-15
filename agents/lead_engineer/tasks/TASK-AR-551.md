---
id: TASK-AR-551
display_id: TASK-AR-551
task_uid: 7d63f433-a221-46b2-b36e-5cf3b44f0452
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-15T13:45:18+09:00
status: completed
resolution: done
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - i18n
  - localization
started_at: 2026-06-15T13:45:18+09:00
completed_at: 2026-06-15T13:45:18+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-546-556.md
  - reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md
---

# TASK-AR-551 - i18n hardening (errors, locale formatting, external resources)

## Goal

- i18n covers UI chrome (ko/en) but error messages are hardcoded English and there is no locale-aware date/number formatting. Extend coverage and move strings out of inline Python.

## Scope

### Input
- `src/agent_runtime/ui_state.py` `lookup_i18n()`/`build_i18n()`; ~199 `data-i18n` usages.
- Verification cases VC-UII-2/3/4.

### Process
- Translate error/validation messages; add locale-aware date/number formatting.
- Externalize translation tables to resource files with a load path (keep inline fallback).

### Output
- Expanded i18n coverage + locale formatting + external resource files.

## Acceptance Criteria

- Error messages localize for ko/en; missing keys fall back to a default (no blanks).
- Dates/numbers render per locale.
- Translations load from resource files; build_i18n still works as fallback.

## Evidence Targets

- i18n diff + tests for VC-UII cases.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`.
