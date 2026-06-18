# Beta Tester Gotchas

## Smoke Is Not Exploration

Opening the page, checking that a selector exists, or taking one screenshot is
not a Beta round. A valid round must include user-like actions plus at least one
edge or recovery scenario.

## DOM Presence Is Not Visibility

Do not accept `textContent`, hidden nodes, or inactive panes as proof that the
user can see or use something. Verify the active view, visible focus, and the
actual rendered state. For tabbed UIs, check the active pane selector, not just
that the pane exists in the document.

## Clean Rounds Need Evidence

"No bugs found" is only useful when it names what was tried. Record navigation,
inputs, viewport, refresh/back behavior, and evidence paths in `ROUNDS.md`.

## User Language First

Write what a user saw and did. Avoid implementation terms such as function names,
selectors, stack traces, state objects, or suspected root causes. Put technical
logs under evidence only when QA needs them.

## Browser Instability Is A Blocker, Not A Pass

If browser automation is flaky or unavailable, record the limitation. A unit test
or API probe can support the report, but it cannot replace exploratory UI
evidence for a user-facing change.
