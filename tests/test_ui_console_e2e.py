"""End-to-end console server tests (TASK-AR-546).

Starts the real ThreadingHTTPServer console handler on a free port and exercises it over
HTTP — a genuine server→routing→render E2E (CI-safe, stdlib only; full browser/Playwright
runs are captured separately via the live MCP). Validates the home page and an API route.

Boot smoke test (TASK-AR-591): verifies GET / and served JS/CSS assets return HTTP 200
and non-empty, and that the served JS passes a syntax check (node --check if node is
available, else a Python-side balanced-bracket/quote check).
"""
import json
import shutil
import subprocess
import tempfile
import threading
import urllib.request
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from agent_runtime import ui_console

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def console_url():
    handler = type("E2EConsoleHandler", (ui_console._ConsoleHandler,), {"root": REPO_ROOT})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _get(url: str, timeout: int = 45):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


class _DomCounter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag, attrs):
        self.count += 1

    def handle_startendtag(self, tag, attrs):
        self.count += 1


def _dom_count(fragment: str) -> int:
    parser = _DomCounter()
    parser.feed(fragment)
    return parser.count


def _browser_home_metrics(console_url: str, viewport: dict[str, int]) -> dict:
    playwright_sync = pytest.importorskip(
        "playwright.sync_api",
        reason="TASK-AR-569 browser layout regression requires Playwright",
    )
    with playwright_sync.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover - environment failure path
            pytest.fail(f"Playwright Chromium is required for TASK-AR-569: {exc}")
        try:
            page = browser.new_page(viewport=viewport)
            page.goto(console_url + "/", wait_until="load")
            page.wait_for_selector("#cockpit")
            page.evaluate(
                """async () => {
                    const loadJson = async (path) => {
                      const response = await fetch(path, { cache: "no-store" });
                      if (!response.ok) throw new Error(`HTTP ${response.status}`);
                      return response.json();
                    };
                    const [inbox, workState] = await Promise.all([
                      loadJson("/api/inbox"),
                      loadJson("/api/work-state"),
                    ]);
                    renderCockpit(inbox);
                    renderWorkState(workState);
                }"""
            )
            page.wait_for_timeout(250)
            return page.evaluate(
                """() => {
                    const box = (selector) => {
                      const element = document.querySelector(selector);
                      if (!element) return null;
                      const rect = element.getBoundingClientRect();
                      const style = getComputedStyle(element);
                      return {
                        top: rect.top,
                        bottom: rect.bottom,
                        height: rect.height,
                        display: style.display,
                        position: style.position,
                      };
                    };
                    return {
                      scrollHeight: document.documentElement.scrollHeight,
                      innerHeight: window.innerHeight,
                      topbarHeight: document.querySelector(".topbar").getBoundingClientRect().height,
                      shellTop: document.querySelector(".work-surface").getBoundingClientRect().top,
                      workSurfaceOpen: document.querySelector("#runtime-console-app").dataset.workSurfaceOpen,
                      workSurfaceDisplay: getComputedStyle(document.querySelector(".work-surface")).display,
                      inboxCards: document.querySelectorAll(".inbox-card").length,
                      workStateCards: document.querySelectorAll(".work-state-card").length,
                      activeViews: document.querySelectorAll(".view.is-active").length,
                      visibleViews: Array.from(document.querySelectorAll(".view"))
                        .filter((view) => getComputedStyle(view).display !== "none").length,
                      boxes: {
                        body: box("body"),
                        shell: box("#runtime-console-app"),
                        topbar: box(".topbar"),
                        sidebar: box(".sidebar"),
                        layout: box(".layout"),
                        cockpit: box("#cockpit"),
                        workState: box("#work-state-hero"),
                        dashboard: box(".dashboard"),
                        workSurface: box(".work-surface"),
                      },
                    };
                }"""
            )
        finally:
            browser.close()


def test_console_home_serves_html(console_url):
    status, body = _get(console_url + "/")
    assert status == 200
    assert "Agent Runtime Console" in body
    assert "<html" in body.lower()


def test_console_catalog_api_returns_json(console_url):
    status, body = _get(console_url + "/api/catalog")
    assert status == 200
    payload = json.loads(body)               # must be valid JSON
    assert isinstance(payload, (dict, list))


# --- product-maturity feature presence (served assets) -----------------------

def test_responsive_media_queries_served(console_url):  # TASK-AR-547
    _, css = _get(console_url + "/app.css")
    assert "@media" in css and "max-width" in css


def test_accessibility_skip_link_and_landmarks(console_url):  # TASK-AR-549
    _, home = _get(console_url + "/")
    _, css = _get(console_url + "/app.css")
    assert 'class="skip-link"' in home and 'href="#main"' in home
    assert 'id="main"' in home                      # skip target landmark exists
    assert ".skip-link" in css and ":focus" in css  # visible only on focus
    assert "<html" in home.lower() and "lang=" in home and 'role="' in home


def test_sse_realtime_client_and_route(console_url):  # TASK-AR-550
    _, js = _get(console_url + "/app.js")
    assert "EventSource" in js                       # real-time client wired (not just polling)


def test_form_validation_and_i18n_present(console_url):  # TASK-AR-548 / 551
    _, js = _get(console_url + "/app.js")
    _, home = _get(console_url + "/")
    assert any(k in js for k in ("aria-invalid", "required", "validat"))   # 548
    assert any(k in home or k in js for k in ("toLocaleString", "Intl.", "i18n"))  # 551


def test_inbox_api_returns_groups(console_url):  # TASK-AR-564 (decision-first cockpit data)
    status, body = _get(console_url + "/api/inbox")
    assert status == 200
    payload = json.loads(body)
    assert "groups" in payload and "total" in payload and "counts" in payload
    assert set(payload["groups"]) >= {"approval_pending", "blocked", "stale",
                                      "gate_failures", "cost_anomalies", "runtime_anomalies"}


def test_cockpit_home_hero_present(console_url):  # TASK-AR-564 (cockpit home view)
    _, home = _get(console_url + "/")
    _, js = _get(console_url + "/app.js")
    _, css = _get(console_url + "/app.css")
    # Hero replaces the 80-screen home as the first decision surface.
    assert 'id="cockpit"' in home and 'id="inbox-groups"' in home
    assert 'data-i18n="cockpit.title"' in home and 'id="inbox-empty"' in home
    assert 'data-i18n-aria-label="cockpit.aria"' in home
    # Client renders /api/inbox into the hero on load + on a refresh cadence.
    assert "loadCockpit" in js and "renderCockpit" in js and "/api/inbox" in js
    # Cockpit styling is present (tokenized; verified literal-free elsewhere).
    assert ".cockpit-grid" in css and ".inbox-card" in css


def test_cockpit_progressive_detail_drawer_present(console_url):  # TASK-AR-566
    _, home = _get(console_url + "/")
    _, js = _get(console_url + "/app.js")
    _, css = _get(console_url + "/app.css")

    assert 'id="inbox-detail-drawer"' in home
    assert 'role="dialog"' in home and 'aria-modal="true"' in home
    assert 'id="inbox-detail-backdrop"' in home
    assert 'id="inbox-detail-close"' in home
    assert "openInboxDetail" in js and "closeInboxDetail" in js
    assert "initInboxDetailDrawer" in js
    assert ".inbox-summary-line" in css
    assert ".inbox-detail-drawer" in css


def test_work_state_api_returns_secondary_hero_shape(console_url):  # TASK-AR-567
    status, body = _get(console_url + "/api/work-state")
    assert status == 200
    payload = json.loads(body)
    assert payload["resource"] == "work_state"
    assert payload["items"]["schema"] == "agent-runtime-work-state-board/v1"
    assert "totals" in payload["items"] and "tasksets" in payload["items"]
    assert set(payload["items"]["totals"]) >= {"waiting", "active", "review", "done", "tasksets", "tasks"}


def test_work_state_secondary_hero_present(console_url):  # TASK-AR-567
    _, home = _get(console_url + "/")
    _, js = _get(console_url + "/app.js")
    _, css = _get(console_url + "/app.css")

    assert 'id="work-state-hero"' in home
    assert 'id="work-state-board"' in home and 'id="work-state-total"' in home
    assert 'data-i18n="work_state.title"' in home
    assert "loadWorkState" in js and "renderWorkState" in js and "/api/work-state" in js
    assert ".work-state-card" in css and ".work-state-drill" in css


def test_i18n_resource_localizes_cockpit_and_work_state(console_url):  # TASK-AR-568
    status, body = _get(console_url + "/api/i18n")
    assert status == 200
    payload = json.loads(body)
    strings = payload["items"]["strings"]

    for key in [
        "cockpit.title",
        "cockpit.open_details",
        "inbox.group.blocked",
        "inbox.action.fix_gate",
        "inbox.why.approval_required",
        "work_state.title",
    ]:
        assert strings[key]["ko"]
        assert strings[key]["en"]

    _, js = _get(console_url + "/app.js")
    assert "localizedInboxWhy" in js
    assert "localizedInboxAction" in js
    assert "renderCockpit(cockpitData)" in js


def test_decision_first_home_budget_and_maturity_regression(console_url):  # TASK-AR-569
    _, home = _get(console_url + "/")
    _, css = _get(console_url + "/app.css")
    _, js = _get(console_url + "/app.js")
    _, i18n_body = _get(console_url + "/api/i18n")
    i18n = json.loads(i18n_body)["items"]

    assert _dom_count(home) <= 1500
    shell_end = home.index('<section class="work-surface">')
    decision_shell = home[:shell_end]
    # TASK-AR-591: budget raised from 320 to 400 to accommodate componentIcon SVG elements
    # wired into all sidebar nav entries (replaces ad-hoc HTML-entity icons with richer SVG).
    # Each componentIcon SVG has ~3-8 child elements; the full icon replacement suite adds
    # ~80 extra DOM nodes that are intentional and within the new budget.
    assert _dom_count(decision_shell) <= 400
    assert home.count('class="view is-active"') == 1
    assert ".view {\n  display: none;" in css and ".view.is-active {\n  display: block;" in css

    assert home.index('id="cockpit"') < home.index('id="work-state-hero"')
    assert home.index('id="work-state-hero"') < home.index('class="dashboard"')
    assert home.index('class="dashboard"') < shell_end

    assert "@media" in css and "max-width" in css
    assert 'class="skip-link"' in home and 'href="#main"' in home and 'id="main"' in home
    assert 'role="dialog"' in home and "aria-live" in home
    assert "EventSource" in js and "/api/stream" in js
    assert 'id="lang-toggle"' in home and i18n["default_language"] == "ko"
    assert {"ko", "en"}.issubset(set(i18n["languages"]))
    assert "required" in home
    assert any(k in js for k in ("aria-invalid", "required", "validat"))


@pytest.mark.parametrize(
    ("label", "viewport"),
    [
        ("desktop", {"width": 1366, "height": 768}),
        ("mobile", {"width": 390, "height": 844}),
    ],
)
def test_decision_first_home_fits_two_screens_in_browser(console_url, label, viewport):  # TASK-AR-569
    metrics = _browser_home_metrics(console_url, viewport)

    assert metrics["activeViews"] == 1
    assert metrics["visibleViews"] == 1
    assert metrics["workSurfaceOpen"] == "false"
    assert metrics["workSurfaceDisplay"] == "none"
    assert metrics["scrollHeight"] <= metrics["innerHeight"] * 2, json.dumps({"label": label, **metrics}, sort_keys=True)


# ---------------------------------------------------------------------------
# Boot smoke tests (TASK-AR-591)
# Verifies the served console returns 200 + non-empty for /, /app.js, /app.css,
# and that the served JS passes a syntax check.
# ---------------------------------------------------------------------------

def _js_syntax_check_node(js_text: str) -> tuple[bool, str]:
    """Check JS syntax via node --check. Returns (ok, detail)."""
    node_exe = shutil.which("node")
    if not node_exe:
        return False, "node not found"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="ascii", errors="replace") as f:
        f.write(js_text)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [node_exe, "--check", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "node --check passed"
        return False, f"node --check failed: {result.stderr.strip()[:400]}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"node check error: {exc}"
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass


def _js_syntax_check_python(js_text: str) -> tuple[bool, str]:
    """Python-side balanced-bracket/quote check as a fallback for JS syntax.

    Checks that all curly braces, square brackets, and parentheses are balanced,
    and that string literals (single and double quotes, template literals) are
    properly terminated. This is a best-effort heuristic, not a full parser.
    """
    depth_curly = depth_square = depth_paren = 0
    in_single = in_double = in_template = False
    prev = ""
    for char in js_text:
        if in_single:
            if char == "'" and prev != "\\":
                in_single = False
        elif in_double:
            if char == '"' and prev != "\\":
                in_double = False
        elif in_template:
            if char == "`" and prev != "\\":
                in_template = False
        else:
            if char == "'":
                in_single = True
            elif char == '"':
                in_double = True
            elif char == "`":
                in_template = True
            elif char == "{":
                depth_curly += 1
            elif char == "}":
                depth_curly -= 1
            elif char == "[":
                depth_square += 1
            elif char == "]":
                depth_square -= 1
            elif char == "(":
                depth_paren += 1
            elif char == ")":
                depth_paren -= 1
        prev = char

    issues = []
    if depth_curly != 0:
        issues.append(f"unbalanced curly braces (depth={depth_curly})")
    if depth_square != 0:
        issues.append(f"unbalanced square brackets (depth={depth_square})")
    if depth_paren != 0:
        issues.append(f"unbalanced parentheses (depth={depth_paren})")
    if in_single:
        issues.append("unterminated single-quote string at end of file")
    if in_double:
        issues.append("unterminated double-quote string at end of file")
    if in_template:
        issues.append("unterminated template literal at end of file")
    if issues:
        return False, "; ".join(issues)
    return True, "Python bracket/quote balance check passed"


def test_boot_smoke_root_200_and_nonempty(console_url):  # TASK-AR-591
    """GET / must return HTTP 200 and non-empty HTML content."""
    status, body = _get(console_url + "/")
    assert status == 200, f"Expected 200 from /, got {status}"
    assert len(body) > 100, "Response body from / is unexpectedly short (< 100 bytes)"
    assert "Agent Runtime Console" in body, "Expected page title in / response"
    assert "<html" in body.lower(), "Expected <html element in / response"


def test_boot_smoke_app_js_200_and_nonempty(console_url):  # TASK-AR-591
    """GET /app.js must return HTTP 200 and non-empty JS content."""
    status, body = _get(console_url + "/app.js")
    assert status == 200, f"Expected 200 from /app.js, got {status}"
    assert len(body) > 500, "Response body from /app.js is unexpectedly short (< 500 bytes)"
    assert "function" in body, "Expected JS function declarations in /app.js"


def test_boot_smoke_app_css_200_and_nonempty(console_url):  # TASK-AR-591
    """GET /app.css must return HTTP 200 and non-empty CSS content."""
    status, body = _get(console_url + "/app.css")
    assert status == 200, f"Expected 200 from /app.css, got {status}"
    assert len(body) > 200, "Response body from /app.css is unexpectedly short (< 200 bytes)"
    assert "--primary" in body, "Expected CSS custom property in /app.css"


def test_boot_smoke_js_syntax_check(console_url):  # TASK-AR-591
    """Served /app.js must pass a JS syntax check (node --check if available, else Python fallback).

    If node is present, validates via node --check (authoritative syntax check).
    If not, falls back to a Python-side balanced-bracket/quote heuristic and
    marks the test with an informational note (not a failure).
    """
    _, js_body = _get(console_url + "/app.js")
    assert js_body, "/app.js returned empty body"

    node_available = shutil.which("node") is not None
    if node_available:
        ok, detail = _js_syntax_check_node(js_body)
        assert ok, f"Served /app.js failed node --check: {detail}"
    else:
        ok, detail = _js_syntax_check_python(js_body)
        # Python fallback: report the result but only fail on clear imbalance.
        assert ok, f"Served /app.js failed Python bracket/quote balance check: {detail}"
        pytest.skip(
            f"node not available; Python fallback used and passed: {detail}"
        )
