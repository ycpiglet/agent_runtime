"""End-to-end console server tests (TASK-AR-546).

Starts the real ThreadingHTTPServer console handler on a free port and exercises it over
HTTP — a genuine server→routing→render E2E (CI-safe, stdlib only; full browser/Playwright
runs are captured separately via the live MCP). Validates the home page and an API route.
"""
import json
import threading
import urllib.request
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
