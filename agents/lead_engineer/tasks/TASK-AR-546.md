---
id: TASK-AR-546
display_id: TASK-AR-546
task_uid: e38bdf8b-01f7-4733-8cdb-e34b4ddce75b
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - testing
  - e2e
  - playwright
---

# TASK-AR-546 - UI end-to-end browser test suite (Playwright)

## Goal

- Close the highest-impact UI testing gap: there are ~326 Python-side UI tests but **no end-to-end browser tests**, so drag-and-drop, keyboard shortcuts, form submission, and polling are unverified in a real browser. Add a Playwright e2e suite that exercises these behaviors.

## Scope

### Input
- `src/agent_runtime/ui_console.py` (served shell/JS), the local server entry point.
- Verification cases VC-UIB-4/5/9, VC-UIF-1..7 in `docs/product-maturity-ui-verification-catalog.md`.

### Process
- Stand up the console against a fixture state; drive it with Playwright (already an available MCP/dev dependency).
- Cover: board render + keyboard drag (Ctrl+D), global search (Ctrl+P), task-create form submit, polling/refresh, theme/motion toggles persist.

### Output
- `tests/e2e/` Playwright specs + a make/CI target; wired into `.github/workflows/test.yml` (non-blocking first, then gating).

## Acceptance Criteria

- e2e suite boots the console headless and passes the covered VC cases.
- Keyboard drag-reorder and global search assert real DOM/state changes (not stubs).
- CI runs the suite on a fixed viewport; failures are reported with traces/screenshots.

## Evidence Targets

- `tests/e2e/*` specs and CI job output.
- Mapping back to VC ids in `docs/product-maturity-ui-verification-catalog.md`.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` (UI testing dimension).
