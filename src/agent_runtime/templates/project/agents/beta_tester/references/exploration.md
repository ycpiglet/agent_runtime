# Beta Tester Exploration Protocol

## Purpose

This protocol turns "try the UI" into a repeatable exploratory round. It is not
QA automation and it is not a smoke test. The goal is to discover behavior that
scripted tests did not anticipate.

## Round Evidence

Write every round to `agents/beta_tester/test_cases/ROUNDS.md`, even when no
bug is found.

Minimum clean-round entry:

```md
## ROUND-YYYY-MM-DD-NNN - CYCLE-NNN / TASK-NNN

- Surface: page, route, or feature changed
- Environment: browser, viewport, OS, server URL
- Actions tried: navigation, inputs, refresh/back, repeated clicks
- Extremes tried: long text, empty values, invalid values, slow/offline state
- Visual evidence: screenshot path or reason unavailable
- Result: clean | BTC-NNN created
- Follow-up: none | QA conversion | regression candidate
```

When a failure is found, create `BTC-NNN.md` immediately and link it from
`ROUNDS.md`. A BTC is user-language evidence; do not include root-cause guesses.

## Required UI Exploration Matrix

For every user-facing UI change, cover all applicable rows:

| Area | Required actions |
| --- | --- |
| Navigation | Open every changed route, switch tabs/views, use back/forward, refresh mid-flow |
| Forms | Empty submit, very long text, whitespace-only, symbols, duplicate submit |
| Commands | Click primary actions once, twice, and while the UI is still updating |
| State | Empty data, large data, malformed/missing data, stale saved state |
| Realtime | Disconnect/reconnect stream, refresh while updates are pending |
| Layout | Desktop, narrow mobile, long labels, zoomed text, horizontal overflow check |
| Accessibility | Keyboard-only path, visible focus, skip link/landmarks when present |
| Errors | Server 4xx/5xx, timeout, offline/slow network if tooling allows |
| Recovery | Reload, reopen, resume from saved state, cancel/escape modal or drawer |

## Playwright Evidence

Use Playwright or the project's browser tool when available, but record actions
in user terms. A screenshot is required for visual, layout, focus, or responsive
issues.

Suggested browser pass:

```bash
python scripts/test_e2e.py
```

If the project uses pytest Playwright instead, run the focused UI E2E command
declared by the task. If a browser is unavailable, record the blocker in
`ROUNDS.md`; do not silently replace exploration with a unit test.

## Promotion To QA

Escalate to QA when:

- the same failure is reproducible twice,
- the failure blocks a primary user flow,
- the result is data loss, broken navigation, inaccessible controls, or a blank screen,
- or the case is valuable as a regression test.

QA converts BTC evidence into `BUG-NNN` and, when useful, an automated regression
test. Beta Tester does not fix or root-cause the issue.
