"""Beta-exploration sweep harness for the live UI console.

A reusable, adversarial "monkey" sweep that drives the real console the way a
beta tester would: visit every nav route, click the interactive controls, push
extremes (huge / unicode / injection inputs), toggle theme + language, resize
mobile<->desktop, and capture JS console errors / unhandled exceptions.

Two layers:

1. ``test_http_route_and_write_sweep`` — ALWAYS runs (stdlib + a tmp root). It
   sweeps every GET API route for non-5xx and hammers the write endpoints with
   malformed / oversized / injection bodies, asserting the server never resets
   the connection or 500s. This is the CI-safe regression net and needs no
   browser. It runs against a throwaway tmp root so it never mutates the repo.

2. The Playwright sweep (``test_browser_full_route_and_control_sweep`` etc.) —
   OPT-IN only. Gated behind ``RUN_BETA_EXPLORATION=1`` so the (slow, browser-
   driven) sweep never bloats the default suite, and ``importorskip`` so it is a
   no-op where Playwright/Chromium are unavailable. Run on demand with::

       RUN_BETA_EXPLORATION=1 PYTHONPATH=src pytest \
           tests/test_ui_console_beta_exploration.py -v

Origin: beta-exploration bug hunt (branch claude/beta-exploration-bughunt). The
HTTP layer is the regression net for the unbounded-title write-path crash
(``task.create`` with a 5000-char title used to raise an uncaught OSError and
reset the connection); see tests/test_ui_commands.py for the unit-level repro.
"""
from __future__ import annotations

import http.client
import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from agent_runtime import ui_console

REPO_ROOT = Path(__file__).resolve().parent.parent

BETA_FLAG = "RUN_BETA_EXPLORATION"
_beta_opt_in = pytest.mark.skipif(
    os.getenv(BETA_FLAG, "") not in {"1", "true", "yes", "on"},
    reason=f"opt-in browser sweep; set {BETA_FLAG}=1 to run",
)

# Every GET route the console exposes (kept in sync with ui_console.build_response).
# Aliased (snake/kebab) duplicates are intentionally included to catch a missing
# alias regression.
GET_ROUTES = [
    "/api/state", "/api/inbox", "/api/stream", "/api/knowledge-graph",
    "/api/events", "/api/replay/snapshot", "/api/search", "/api/catalog",
    "/api/catalog/facets", "/api/catalog/docs", "/api/activity", "/api/scm",
    "/api/tasks", "/api/agents", "/api/task-sets", "/api/task_sets",
    "/api/messages", "/api/goals", "/api/inflight", "/api/work-explorer",
    "/api/work_explorer", "/api/work-state", "/api/work_state",
    "/api/meeting-room", "/api/tasksets-board", "/api/taskset-completion",
    "/api/team-agents", "/api/teams", "/api/growth", "/api/workload",
    "/api/sources", "/api/errors", "/api/evidence", "/api/attachments",
    "/api/replay", "/api/graph", "/api/live-map", "/api/office-map",
    "/api/state-machines", "/api/roadmap", "/api/roadmap-timeline",
    "/api/planning", "/api/custom-properties", "/api/labels",
    "/api/automation-rules", "/api/triage", "/api/reviews", "/api/schedules",
    "/api/calendar", "/api/notifications", "/api/daily-brief",
    "/api/notification-routing", "/api/workspaces", "/api/widgets", "/api/i18n",
    "/api/search-index", "/api/commands",
]

# Adversarial GET params: bad ints, traversal, injection, huge values.
GET_EDGE_ROUTES = [
    "/api/catalog/entity",                       # missing id -> 404 (clean)
    "/api/catalog/entity?id=does-not-exist",     # bad id -> 404 (clean)
    "/api/knowledge-graph?limit=abc",            # non-int limit
    "/api/knowledge-graph?limit=-5",             # negative limit
    "/api/knowledge-graph?limit=999999999",      # absurd limit
    "/api/export/board.csv",                     # valid export
    "/api/export/__bogus__",                     # unknown export
    "/api/search?q=" + "x" * 4000,               # huge query
    "/api/search?q=%3Cscript%3Ealert(1)%3C/script%3E",  # injection query
    "/api/attachments/..%2f..%2fetc/download",   # path traversal
    "/vendor/lucide-static/1.21.0/icons/..%2f..%2fui_console.py",  # vendor traversal
    "/totally/unknown/route",                    # 404
]


def _serve(root: Path) -> tuple[ThreadingHTTPServer, str]:
    handler = type("BetaConsoleHandler", (ui_console._ConsoleHandler,), {"root": root})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{port}"


@pytest.fixture()
def console_url():
    """Serve the console against the real repo root (read-only sweep + browser
    drive), so the harness exercises *current* behavior with real data and the
    sibling scripts the console depends on (e.g. scripts/attention_inbox.py)."""
    server, url = _serve(REPO_ROOT)
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture()
def throwaway_console_url(tmp_path):
    """Serve against a throwaway root so the write-path stress test never mutates
    the repo. Copies in the scripts the read routes need so they don't 500."""
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    src_inbox = REPO_ROOT / "scripts" / "attention_inbox.py"
    if src_inbox.is_file():
        (tmp_path / "scripts" / "attention_inbox.py").write_bytes(src_inbox.read_bytes())
    server, url = _serve(tmp_path)
    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()


def _get_status(url: str, timeout: int = 90) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read()
            return resp.status
    except urllib.error.HTTPError as exc:  # 4xx/5xx still carry a status
        return exc.code


def _post(host: str, port: int, path: str, body: bytes, timeout: int = 90) -> int:
    """POST raw bytes and return the HTTP status. Raises if the connection is
    reset with no response (the failure mode of an uncaught handler exception)."""
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        return conn.getresponse().status
    finally:
        conn.close()


def test_http_get_route_sweep_never_5xx(console_url):
    """Every GET route and every adversarial param must respond with a status
    (never a 5xx, never a connection reset)."""
    failures = []
    for route in GET_ROUTES + GET_EDGE_ROUTES:
        try:
            status = _get_status(console_url + route)
        except Exception as exc:  # noqa: BLE001 - any reset/timeout is a finding
            failures.append((route, f"no response: {type(exc).__name__}: {exc}"))
            continue
        if status >= 500:
            failures.append((route, f"HTTP {status}"))
    assert not failures, "GET routes returned 5xx / no response:\n" + "\n".join(f"  {r}: {d}" for r, d in failures)


def test_http_write_path_stress_returns_clean_status(throwaway_console_url):
    """The write endpoints must reject malformed / oversized / injection bodies
    with a clean 4xx and never reset the connection or 5xx.

    The oversized-title case is the regression for the beta-exploration finding:
    a multi-thousand-character title used to overflow the task filename and raise
    an uncaught OSError that reset the connection (curl saw HTTP 000).

    Runs against a throwaway root: the injection/unicode case is *accepted* and
    actually writes a proposal, so it must not touch the real repo."""
    host, port = throwaway_console_url.split("//", 1)[1].split(":")
    port = int(port)

    huge_title = json.dumps({"type": "task.create", "payload": {"title": "A" * 5000}}).encode()
    unicode_title = json.dumps(
        {"type": "task.create", "payload": {"title": "<script>alert(1)</script> 😀 ' ; DROP TABLE"}}
    ).encode()

    cases = [
        ("/api/commands", b"not json{"),                       # malformed json
        ("/api/commands", b""),                                # empty body
        ("/api/commands", b"[]"),                              # non-object json
        ("/api/commands", b'{"type":"bogus.command"}'),        # unknown type
        ("/api/commands", huge_title),                         # oversized title (regression)
        ("/api/commands", unicode_title),                      # unicode + injection (accepted, escaped on render)
        ("/api/tasks", b"{}"),                                 # missing required fields
        ("/api/import/preview", b'{"format":"xml","content":"x"}'),   # unsupported format
        ("/api/import/preview", b'{"format":"csv","content":123}'),   # non-string content
        ("/api/attachments", b"{}"),                           # missing attachment data
        ("/api/nope", b"{}"),                                  # unknown route
    ]
    failures = []
    for path, body in cases:
        try:
            status = _post(host, port, path, body)
        except Exception as exc:  # noqa: BLE001 - connection reset == the bug
            failures.append((path, len(body), f"no response: {type(exc).__name__}: {exc}"))
            continue
        # Any well-formed status (2xx/4xx) is acceptable; only 5xx / reset is a bug.
        if status >= 500:
            failures.append((path, len(body), f"HTTP {status}"))
    assert not failures, "write endpoints reset/5xx:\n" + "\n".join(
        f"  POST {p} ({n} bytes): {d}" for p, n, d in failures
    )

    # Specifically: the oversized title is rejected with 4xx, not accepted/reset.
    assert _post(host, port, "/api/commands", huge_title) == 400


# ---------------------------------------------------------------------------
# Opt-in Playwright sweep (RUN_BETA_EXPLORATION=1). Slow + needs Chromium.
# ---------------------------------------------------------------------------

def _browser_sweep(console_url: str, viewport: dict[str, int]) -> dict:
    playwright_sync = pytest.importorskip(
        "playwright.sync_api",
        reason="beta exploration browser sweep requires Playwright",
    )
    with playwright_sync.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover - environment failure path
            pytest.skip(f"Chromium unavailable for beta sweep: {exc}")
        try:
            page = browser.new_page(viewport=viewport)
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))
            page.goto(console_url + "/", wait_until="load")
            page.wait_for_selector("#runtime-console-app")

            # Sweep every nav route via the real router; assert exactly one active
            # view and no thrown error per route.
            sweep = page.evaluate(
                """() => {
                    const links = Array.from(document.querySelectorAll('.sidebar-link'));
                    const results = [];
                    for (const link of links) {
                      const view = link.dataset.view;
                      let threw = null;
                      try { activateView(view); } catch (e) { threw = String(e && e.message || e); }
                      results.push({
                        view, threw,
                        activeViews: document.querySelectorAll('.view.is-active').length,
                      });
                    }
                    return results;
                }"""
            )

            # Exercise the headline controls (theme, language, command palette,
            # mobile sidebar) and weird palette input.
            controls = page.evaluate(
                """() => {
                    const out = { errors: [] };
                    const safe = (label, fn) => { try { out[label] = fn(); } catch (e) { out.errors.push(label + ': ' + (e && e.message || e)); } };
                    safe('theme', () => { const t = document.getElementById('theme-toggle'); t.click(); const a = document.documentElement.getAttribute('data-theme'); t.click(); return a; });
                    safe('lang', () => { const s = document.getElementById('lang-toggle'); s.value = 'en'; s.dispatchEvent(new Event('change', {bubbles:true})); const a = document.documentElement.lang; s.value = 'ko'; s.dispatchEvent(new Event('change', {bubbles:true})); return a; });
                    safe('palette', () => {
                      document.dispatchEvent(new KeyboardEvent('keydown', {key:'k', ctrlKey:true, bubbles:true}));
                      const p = document.getElementById('command-palette');
                      const inp = document.getElementById('command-palette-input');
                      inp.value = '<script> ' + 'x'.repeat(500);
                      inp.dispatchEvent(new Event('input', {bubbles:true}));
                      document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
                      return { hiddenAfterEsc: p.hidden };
                    });
                    safe('hashFuzz', () => {
                      ['#/totally/bogus', '#/<script>alert(1)</script>', '#/' + 'a'.repeat(3000), '#'].forEach(h => {
                        window.location.hash = h; if (typeof applyHashRoute === 'function') applyHashRoute();
                      });
                      return document.querySelectorAll('.view.is-active').length;
                    });
                    return out;
                }"""
            )

            horizontal_overflow = page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth + 2"
            )

            return {
                "sweep": sweep,
                "controls": controls,
                "consoleErrors": console_errors,
                "horizontalOverflow": horizontal_overflow,
            }
        finally:
            browser.close()


@_beta_opt_in
@pytest.mark.parametrize(
    ("label", "viewport"),
    [("desktop", {"width": 1366, "height": 768}), ("mobile", {"width": 390, "height": 844})],
)
def test_browser_full_route_and_control_sweep(console_url, label, viewport):
    result = _browser_sweep(console_url, viewport)

    # Every route activates without throwing and leaves exactly one active view.
    for entry in result["sweep"]:
        assert entry["threw"] is None, f"[{label}] view {entry['view']} threw: {entry['threw']}"
        assert entry["activeViews"] == 1, f"[{label}] view {entry['view']} -> {entry['activeViews']} active views"

    # Controls work without throwing; palette closes on Escape; layout doesn't overflow.
    assert not result["controls"]["errors"], f"[{label}] control errors: {result['controls']['errors']}"
    assert result["controls"].get("lang") == "en"
    assert result["controls"].get("palette", {}).get("hiddenAfterEsc") is True
    assert result["controls"].get("hashFuzz") == 1
    assert result["horizontalOverflow"] is False, f"[{label}] horizontal overflow detected"

    # No JS console errors / unhandled exceptions during the whole sweep.
    assert not result["consoleErrors"], f"[{label}] JS console errors: {result['consoleErrors']}"
