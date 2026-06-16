---
type: review
id: REVIEW-2026-06-16-task-ar-565-nav-prune-core7
audience: owner
status: pass
signal: pass
score: 100
task_ref: TASK-AR-565
task_set_id: TASKSET-AR-DECISION-FIRST-CONSOLE-IA
tags: [ui, decision-first, navigation, review]
---

# REVIEW - TASK-AR-565 Nav Prune Core 7

## Bottom Line

Unit 3 follows the approved spec instead of re-deciding the IA: the visible first-level
sidebar is now Home, Work, Agents, Decisions, Records, Search, and More. Existing detail
routes remain linked behind collapsed More.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Core 7 visible nav | pass | Playwright labels: Home, Work, Agents, Decisions, Records, Search, More |
| More default state | pass | `.sidebar-more.open` was false on load |
| Dead-link guard | pass | 27 More links checked; every `data-view` had a matching `view-*` container |
| Route/API smoke | pass | `/`, `/app.css`, `/api/tasks`, `/api/inbox`, `/api/search?q=TASK-AR-565` returned 200 |
| Tests | pass | `148 passed` in `tests/test_ui_console.py`; `8 passed` in `tests/test_ui_console_e2e.py` |

## Decision

- Use the spec core 7 exactly: Home, Work, Agents, Decisions, Records, Search, More.
- Map Decisions to the existing meeting/review/seminar surface (`data-view="meeting"`, existing route `comms/meetings`) so the old route stays alive.
- Map Search to a lightweight console search view backed by the existing `/api/search`; no new storage or backend surface.
- Move non-core Work, Agents, Comms, Records, and Ops routes into collapsed More groups.
- Preserve current route strings where they already existed; More is disclosure, not deletion.

## Action Board

| Item | Status | Notes |
| --- | --- | --- |
| Sidebar IA | done | Core links are first-level; detail links are nested under More |
| Search view | done | Uses existing search API and result renderer |
| More activation | done | Selecting a More item opens More so the active item remains visible |
| Visual evidence | done | `reviews/artifacts/task-ar-565-nav-core7.png` |

## Verification

- `python -m pytest tests/test_ui_console.py -q`
- `python -m pytest tests/test_ui_console_e2e.py -q`
- Python Playwright visual check against `http://127.0.0.1:8766/`
