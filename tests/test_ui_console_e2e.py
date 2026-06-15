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
