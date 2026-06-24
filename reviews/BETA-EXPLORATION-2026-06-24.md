---
type: beta-exploration-bug-catalog
title: UI Console Beta Exploration Bug Catalog 2026-06-24
date: 2026-06-24
status: complete
signal: pass
explorer_agent_id: beta-tester-ui-console-20260624
branch: claude/beta-exploration-bughunt
harness: live-browser (Playwright/Chromium) + HTTP fallback sweep
---

# UI Console Beta Exploration — Bug Catalog (2026-06-24)

Adversarial beta-test of the live console (`src/agent_runtime/ui_console.py` +
`ui_console_assets.py`) on branch `claude/beta-exploration-bughunt`, served from
the current worktree (cockpit-default home, new IA, i18n; sprites not live).

## How it was driven

- **Live browser harness RAN** (not a fallback): Playwright + headless Chromium
  drove the real served page — navigated every route, clicked controls, fuzzed
  inputs, resized mobile/desktop, captured JS console + pageerror events.
- **HTTP sweep** complemented it: all GET API routes + adversarial params, and
  every write endpoint (POST/PATCH) with malformed / empty / oversized / unicode
  / injection bodies, asserting no 5xx / connection reset.
- Coverage: 33 nav routes (home/work/agents/comms/records/ops + More), the
  cockpit hero, work-state hero, command palette (Ctrl+K), theme + language
  toggles, calendar controls, knowledge-graph + agent-map SVG render, mobile
  sidebar/scrim, hash routing, and 70 API endpoints.

## Severity summary

| Severity | Count | Items |
| --- | --- | --- |
| High | 1 | B-01 (write-path crash on oversized title) — FIXED |
| Medium | 2 | B-02 (`/api/inbox` 500 when scripts absent), B-03 (SSE single-shot reconnect + double-poll) |
| Low | 1 | B-04 (handler lacks top-level exception guard) |
| Info / not-a-bug | 5 | see "Verified robust" |

Net: 1 bug fixed with TDD in this PR; 3 listed for Owner/triage (design or risk
judgment needed); strong baseline robustness otherwise.

## Findings (prioritized)

### B-01 — HIGH — `task.create` crashes the request on an oversized title (FIXED)

- **Area:** write path — `ui_commands._create_task` → HTTP `POST /api/commands`.
- **Repro:** `POST /api/commands` with
  `{"type":"task.create","payload":{"title":"A"*5000}}` (any title > ~200 chars).
- **Observed (before fix):** server raised an uncaught `OSError`/`FileNotFoundError`
  (`[Errno 22]` on Windows; `ENAMETOOLONG` on Linux) because the task filename is
  built as `TASK-UI-<ts>-<slug(title)>.md` with no length bound, overflowing the
  OS path limit. The exception propagated through `build_response` → `do_POST`
  with no guard, so the connection was reset with **no HTTP response** (curl saw
  `HTTP 000`) and a full traceback dumped to stderr. Even a 100KB body reproduced.
- **Expected:** clean `400` with a validation error; server stays up.
- **Evidence:** stderr `FileNotFoundError: ...TASK-UI-...aaaa....md` (filename
  hundreds of chars long).
- **Fix (this PR):** added `TASK_TITLE_MAX_LENGTH = 200` bound in
  `_create_task`; oversized titles now return
  `{"status":"failed","errors":["title is too long: N chars (max 200)"]}` (HTTP
  400). TDD: `tests/test_ui_commands.py::test_submit_create_task_rejects_overlong_title_without_crashing`
  (red → green). Verified live: `POST` now returns 400, server stays alive, no
  traceback.

### B-02 — MEDIUM — `/api/inbox` 500s (uncaught `ModuleNotFoundError`) when `scripts/attention_inbox.py` is absent

- **Area:** `ui_console.build_response` — `/api/inbox` route.
- **Repro:** serve the console with a root whose `scripts/` lacks
  `attention_inbox.py`, then `GET /api/inbox`.
- **Observed:** uncaught `ModuleNotFoundError: No module named 'attention_inbox'`
  (the route does `sys.path.insert(0, root/scripts)` then `import attention_inbox`).
  Propagates to a 500 / connection reset. On the page this surfaces as a failed
  `loadCockpit` and a JS console error.
- **Expected:** a graceful empty/again-later inbox payload (or a clean 503), not
  a 500, when the helper script is missing.
- **Impact:** narrow — the real repo/template always ships `scripts/attention_inbox.py`,
  so it does not hit normal deployments. But the cockpit is the *default home*, so
  a missing/renamed script breaks the first screen hard with no fallback.
- **Triage:** NOT fixed — wrap the import in try/except with a typed empty-inbox
  fallback, or make the dependency explicit. Low-risk but touches the cockpit
  data contract; flagged for Owner decision on the fallback shape.

### B-03 — MEDIUM — SSE `/api/stream` is single-shot; EventSource reconnect-storms and double-loads `/api/state`

- **Area:** `ui_console._sse_response` + `connectEventStream()` in assets.
- **Observed:** `/api/stream` returns ONE `event: state` frame then closes the
  connection. The browser `EventSource` treats every close as an error and
  auto-reconnects (~3s), so it polls one snapshot per reconnect indefinitely —
  and the status pill flickers `live` → `polling`. This runs *in addition to*
  `setInterval(loadState, 4000)` + cockpit (8s) + work-state (15s) polls, so the
  expensive `/api/state` (full repo scan) is fetched far more often than intended;
  overlapping fetches show as `net::ERR_ABORTED` in the network log.
- **Expected:** either a true long-lived SSE stream that pushes on change, or
  drop the SSE entirely and rely on the interval poll (don't pay both).
- **Impact:** perf/cost, not correctness — masked by the state-cache prewarm, but
  on a large store this is wasteful and the indicator is misleading.
- **Triage:** NOT fixed — this is a design decision (real streaming vs. poll-only).

### B-04 — LOW — request handlers have no top-level exception guard

- **Area:** `ui_console.do_GET/do_POST/do_PATCH` → `build_response`.
- **Observed:** `build_response` and the per-command handlers are not wrapped in
  try/except, so ANY unexpected handler exception (B-01, B-02, or a future one)
  resets the connection with no response instead of returning a 500 with a body.
- **Expected:** a top-level guard returning a clean `500 {"status":"error",...}`
  so one bad input can never silently drop a connection or leak a traceback.
- **Triage:** NOT fixed — a defensive wrapper is reasonable but is a broader
  hardening change (and could mask errors if done carelessly); flagged for Owner.
  Note: B-01's root-cause fix (input validation) is the preferred first line of
  defense; this guard would be defense-in-depth.

## Verified robust (info — adversarial tests that PASSED, no bug)

- **All 33 routes** activate with exactly one active/visible view, zero JS errors
  (desktop + mobile). View-switch invariant holds under rapid repeated switching.
- **GET sweep:** 70 API routes — no 5xx. Bad ints (`limit=abc/-5/huge`),
  traversal (`..%2f..`), injection, and 4000-char queries are all handled (404 /
  clean JSON), never a crash.
- **Write validation:** malformed JSON, empty body, non-object body, unknown
  command type, missing fields → clean `400` (audit COMMAND record still written,
  by design). Unknown POST route → `404`.
- **Stored-XSS:** a `<script>` task title is accepted (proposal-only) but rendered
  everywhere via `escapeHtml(...)` — no XSS. Filename is slugified to safe chars
  (no path injection).
- **Command palette:** Ctrl+K opens; filter works; `<script>`/huge/unicode query
  shows "No matching"; Escape closes. No injection.
- **i18n:** language toggle (`<select>`) switches ko↔en across all copy and
  persists (`agent-runtime-language`); default is `ko`. No un-keyed English leak
  detected in the rendered DOM.
- **Theme toggle:** light↔dark, persists (`agent-runtime-theme`), `aria-pressed`
  correct.
- **Responsive:** mobile (390px) has no horizontal overflow; hamburger + scrim
  open/close the sidebar; resize desktop↔mobile clean.
- **Hash routing:** bogus routes fall back to board; `<script>` / `img onerror` /
  5000-char hashes / `select=` injection are safe (CSS.escape), always 1 active view.
- **Heavy views:** knowledge-graph renders a real D3/dagre SVG (140/1215 entities,
  332 edges); agent-map renders 70 SVG nodes; calendar prev/next/today/week/month/
  reserve survive 45 rapid clicks. All zero-error.
- **A11y baseline:** no unnamed buttons, no unlabeled inputs, no missing `alt`,
  no duplicate IDs.

## Meta-note for future beta runs

`task.create` (and other write commands) write REAL files to the served root
(task file + `.ui_outbox/` command record + `BACKLOG-BOARD.md`/`ARCHIVE-INDEX.md`
re-sync) — stress-testing write endpoints against the repo mutates it. The
reusable harness (`tests/test_ui_console_beta_exploration.py`) therefore runs
write-path stress against a throwaway tmp root. Test artifacts created during
this manual run were cleaned up; the working tree contains only the intended
source/test/report changes.

## Deliverables in this PR

- Fix: `src/agent_runtime/ui_commands.py` (B-01 title bound).
- TDD test: `tests/test_ui_commands.py::test_submit_create_task_rejects_overlong_title_without_crashing`.
- Reusable harness: `tests/test_ui_console_beta_exploration.py` (HTTP sweep
  always-on as a CI-safe regression net; Playwright sweep opt-in behind
  `RUN_BETA_EXPLORATION=1`).
- This report.
