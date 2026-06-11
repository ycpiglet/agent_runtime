---
type: review
id: REVIEW-2026-06-11-agent-runtime-task-ar-281-evidence-event-panes
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [ui-console, ui-design, evidence, events, task-ar-281, verification]
---

# TASK-AR-281 Evidence And Event Pane Closeout

## Bottom Line

- Summary: `TASK-AR-281` is complete for the evidence, event, error, and replay pane hierarchy scope.
- Output: Events, Errors, Evidence, and Replay now render as audit cards with visible metadata labels and pass/warn/fail left-rail treatment.
- Boundary: this closes audit/evidence pane treatment only; graph, planner, source, and write surfaces remain tracked by `TASK-AR-282` through `TASK-AR-284`.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Audit hierarchy | pass | `renderEvents()` and `renderEvidence()` now emit `.audit-card` surfaces |
| Severity treatment | pass | `.audit-card.pass`, `.audit-card.warn`, and `.audit-card.fail` are styled explicitly |
| Evidence priority | pass | `.evidence-card` promotes evidence path/source as the primary card object |
| Event filters | pass | `event-filter-type`, `event-filter-agent`, `event-filter-task`, `event-filter-goal`, and `event-filter-search` remain in the HTML shell |
| Route compatibility | pass | Existing `/api/events` filter test still passes |
| Focused tests | pass | `python -m pytest tests/test_ui_console.py tests/test_ui_state.py tests/test_ui_commands.py -q`: `43 passed` |
| Syntax check | pass | `python -m py_compile src/agent_runtime/ui_console.py` |
| Browser verification | pass | Headless Playwright on `http://127.0.0.1:8769/`: desktop `1440x1000` and mobile `390x844` had no horizontal overflow and no console errors/warnings |

## Insight

- The previous evidence/event UI treated audit records as generic list rows, which made source, task, goal, and severity hard to scan.
- The new audit card pattern keeps the dense console layout but makes every audit object carry its own Event/Evidence/Replay, Severity, Actor, Task, Goal, and Source labels.
- Event filtering remains independent of the visual treatment, so existing route semantics and UI filter controls are preserved.

## Decision

- Mark `TASK-AR-281` completed.
- Keep `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` active and continue with `TASK-AR-282` next.
- Preserve the existing event/evidence/replay data contracts; this change is presentation-only.

## Action Board

| Item | State | Next |
| --- | --- | --- |
| `TASK-AR-281` | completed | Archive from live board after board regeneration |
| `TASK-AR-282` | planned | Apply operator-console treatment to map, planner, source, and write panes |
| UI server | stopped | Local verification used `http://127.0.0.1:8769/`; server PID `20500` was stopped after checks |

## Risks / Blockers

- Risk: `auditToneClass()` intentionally derives tone from record text when a canonical severity is missing; future state adapters can replace this with explicit severity fields.
- Risk: long source paths are now more prominent; cards rely on existing overflow-wrap behavior to keep mobile layout stable.
- Blocker: none for `TASK-AR-281` local scope.

## Next Steps

- Start `TASK-AR-282` with a fresh claim before changing graph, planner, source, or write panes.
- Continue using headless Playwright or Browser tooling for desktop and mobile visual checks.
- Keep Owner-facing review entries in `owner-docs.yml` as each pane-level closeout lands.
