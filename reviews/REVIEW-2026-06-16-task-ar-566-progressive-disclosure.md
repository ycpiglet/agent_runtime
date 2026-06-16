---
type: review
id: REVIEW-2026-06-16-task-ar-566-progressive-disclosure
audience: owner
status: pass
signal: pass
score: 100
task_ref: TASK-AR-566
task_set_id: TASKSET-AR-DECISION-FIRST-CONSOLE-IA
tags: [ui, decision-first, progressive-disclosure, review]
---

# REVIEW - TASK-AR-566 Progressive Disclosure Detail Panel

## Bottom Line

The Decision Cockpit home now keeps attention groups compact: each card shows a count,
a one-line summary, and an explicit details action. Full attention item content opens in
a keyboard-accessible side drawer instead of expanding inline on the home surface.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Compact home | pass | Inline `.inbox-items`/top-3 rendering removed; cards use `.inbox-summary-line` |
| Detail disclosure | pass | `#inbox-detail-drawer` dialog with backdrop, close button, and list region |
| Keyboard escape | pass | Escape closes only when drawer exists and is visible |
| Focus return | pass | opener stored in `inboxDrawerPreviousFocus` and restored on close |
| Tests | pass | `149 passed` in `tests/test_ui_console.py`; `9 passed` in `tests/test_ui_console_e2e.py` |

## Decision

- Keep the cockpit hero as the first decision surface, but do not make the home page
  carry full item detail.
- Use a focus-managed drawer for full list review so the cockpit remains scannable and
  the existing detail views remain available.
- Preserve existing `/api/inbox` data shape; this task only changes presentation and
  local interaction behavior.
- Keep served JS ASCII-safe for the existing inbox test contract by escaping Korean
  command helper strings in source.

## Action Board

| Item | Status | Notes |
| --- | --- | --- |
| Compact group cards | done | Count, one-line summary, and Open details button |
| Drawer shell | done | Dialog/backdrop/list markup in home HTML |
| Drawer behavior | done | Open, close, Escape, and focus return wired in app JS |
| Regression coverage | done | Static contract test plus server E2E asset test |

## Verification

- `$env:PYTHONPATH=(Resolve-Path src).Path; python -m pytest tests/test_ui_console.py -q`
- `$env:PYTHONPATH=(Resolve-Path src).Path; python -m pytest tests/test_ui_console_e2e.py -q`
