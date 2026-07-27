from __future__ import annotations

import json
import sys
import threading
import traceback
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlparse

from . import ui_commands
from . import ui_console_assets
from . import ui_export
from . import ui_state


@dataclass(frozen=True)
class ConsoleResponse:
    status: int
    content_type: str
    body: bytes


HTML = ui_console_assets.HTML
CSS = ui_console_assets.CSS
JS = ui_console_assets.JS

_PACKAGE_ROOT = Path(__file__).resolve().parent
_VENDOR_ASSETS: dict[str, tuple[Path, str]] = {
    "/vendor/dagre/3.0.0/dagre.min.js": (
        _PACKAGE_ROOT / "vendor" / "dagre" / "3.0.0" / "dagre.min.js",
        "application/javascript; charset=utf-8",
    ),
    "/vendor/d3-quadtree/3.0.1/d3-quadtree.min.js": (
        _PACKAGE_ROOT / "vendor" / "d3-quadtree" / "3.0.1" / "d3-quadtree.min.js",
        "application/javascript; charset=utf-8",
    ),
    "/vendor/d3-dispatch/3.0.1/d3-dispatch.min.js": (
        _PACKAGE_ROOT / "vendor" / "d3-dispatch" / "3.0.1" / "d3-dispatch.min.js",
        "application/javascript; charset=utf-8",
    ),
    "/vendor/d3-timer/3.0.1/d3-timer.min.js": (
        _PACKAGE_ROOT / "vendor" / "d3-timer" / "3.0.1" / "d3-timer.min.js",
        "application/javascript; charset=utf-8",
    ),
    "/vendor/d3-force/3.0.0/d3-force.min.js": (
        _PACKAGE_ROOT / "vendor" / "d3-force" / "3.0.0" / "d3-force.min.js",
        "application/javascript; charset=utf-8",
    ),
    "/vendor/geist/1.7.2/fonts/geist-sans/Geist-Variable.woff2": (
        _PACKAGE_ROOT / "vendor" / "geist" / "1.7.2" / "fonts" / "geist-sans" / "Geist-Variable.woff2",
        "font/woff2",
    ),
    "/vendor/geist/1.7.2/fonts/geist-sans/Geist-Italic[wght].woff2": (
        _PACKAGE_ROOT / "vendor" / "geist" / "1.7.2" / "fonts" / "geist-sans" / "Geist-Italic[wght].woff2",
        "font/woff2",
    ),
    "/vendor/geist/1.7.2/fonts/geist-mono/GeistMono-Variable.woff2": (
        _PACKAGE_ROOT / "vendor" / "geist" / "1.7.2" / "fonts" / "geist-mono" / "GeistMono-Variable.woff2",
        "font/woff2",
    ),
    "/vendor/geist/1.7.2/fonts/geist-mono/GeistMono-Italic[wght].woff2": (
        _PACKAGE_ROOT / "vendor" / "geist" / "1.7.2" / "fonts" / "geist-mono" / "GeistMono-Italic[wght].woff2",
        "font/woff2",
    ),
}
_LUCIDE_ICON_VENDOR_PREFIX = "/vendor/lucide-static/1.21.0/icons/"
_LUCIDE_ICON_VENDOR_ROOT = _PACKAGE_ROOT / "vendor" / "lucide-static" / "1.21.0" / "icons"

def _bytes(text: str) -> bytes:
    return text.encode("utf-8")


def _vendor_asset_response(request_path: str) -> ConsoleResponse | None:
    decoded_path = unquote(request_path)
    entry = _VENDOR_ASSETS.get(request_path) or _VENDOR_ASSETS.get(decoded_path)
    if entry is None:
        if not decoded_path.startswith(_LUCIDE_ICON_VENDOR_PREFIX):
            return None
        filename = decoded_path.removeprefix(_LUCIDE_ICON_VENDOR_PREFIX)
        if "/" in filename or "\\" in filename or not filename.endswith(".svg"):
            return ConsoleResponse(404, "text/plain; charset=utf-8", b"vendor asset missing\n")
        path = _LUCIDE_ICON_VENDOR_ROOT / filename
        if not path.is_file():
            return ConsoleResponse(404, "text/plain; charset=utf-8", b"vendor asset missing\n")
        return ConsoleResponse(200, "image/svg+xml; charset=utf-8", path.read_bytes())
    path, content_type = entry
    if not path.is_file():
        return ConsoleResponse(404, "text/plain; charset=utf-8", b"vendor asset missing\n")
    return ConsoleResponse(200, content_type, path.read_bytes())


def _json_response(payload: object, status: int = 200) -> ConsoleResponse:
    return ConsoleResponse(
        status=status,
        content_type="application/json; charset=utf-8",
        body=_bytes(json.dumps(payload, ensure_ascii=False, indent=2)),
    )


# B-03: the SSE endpoint is single-shot (one frame then close). A browser
# EventSource treats every close as an error and auto-reconnects at its default
# (~3s), which would re-fetch the heavy /api/state on every reconnect on top of
# the interval poll. Advertising a long client retry interval throttles that
# reconnect cadence to at/under the interval poll so it can't storm.
_SSE_RETRY_MS = 60000


def _sse_response(payload: object) -> ConsoleResponse:
    body = (
        f"retry: {_SSE_RETRY_MS}\n"
        + "event: state\n"
        + "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "\n\n"
    )
    return ConsoleResponse(200, "text/event-stream; charset=utf-8", _bytes(body))


# The attention-inbox groups (kept in sync with scripts/attention_inbox.py's
# GROUP_ORDER) so the degraded fallback returns the same shape the cockpit
# expects. TASK-AR-630: added gate_watch and the previously-missing unowned.
_INBOX_GROUP_ORDER = (
    "approval_pending",
    "blocked",
    "gate_failures",
    "gate_watch",
    "runtime_anomalies",
    "cost_anomalies",
    "stale",
    "unowned",
)


def _degraded_inbox_payload() -> dict[str, object]:
    """A valid, empty-but-shaped inbox payload used when the inbox helper/data is
    unavailable, so the cockpit default home renders an empty state instead of a
    500. ``degraded`` lets the UI distinguish "nothing to do" from "couldn't load"."""
    return {
        "groups": {group: [] for group in _INBOX_GROUP_ORDER},
        "counts": {group: 0 for group in _INBOX_GROUP_ORDER},
        "total": 0,
        "degraded": True,
    }


def _inbox_response(root_path: Path) -> ConsoleResponse:
    """B-02: serve the attention inbox, degrading gracefully when the derived-read
    helper (scripts/attention_inbox.py) is missing or unloadable. The cockpit is
    the default home, so a missing/renamed script must NOT 500 the first screen —
    it returns a valid empty/degraded payload (200) instead."""
    scripts = str(root_path / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import attention_inbox  # noqa: PLC0415 - lazy, optional sibling script
        return _json_response(attention_inbox.inbox(root_path))
    except Exception:  # noqa: BLE001 - any failure degrades to an empty inbox
        # Log the cause to stderr (don't silently swallow) but keep the home alive.
        traceback.print_exc()
        return _json_response(_degraded_inbox_payload())


def _decode_json_body(body: bytes | None) -> tuple[dict[str, object], list[str]]:
    if not body:
        return {}, []
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"invalid json body: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["json body must be an object"]
    return payload, []


def _command_response(root_path: Path, command: dict[str, object]) -> ConsoleResponse:
    result = ui_commands.submit_command(root_path, command)
    return _json_response(result, status=400 if result.get("status") == "failed" else 202)


def _attachment_upload_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    """Validate + persist an uploaded attachment, returning the evidence record."""
    try:
        data = ui_state.decode_attachment_payload(payload.get("content_b64") or payload.get("content"))
        record = ui_state.save_attachment(
            root_path,
            filename=payload.get("filename"),
            content_type=payload.get("content_type"),
            data=data,
            task_id=payload.get("task_id"),
            message_id=payload.get("message_id"),
            actor=payload.get("actor"),
        )
    except ui_state.AttachmentError as exc:
        return _json_response({"status": "failed", "errors": [str(exc)]}, status=400)
    return _json_response({"status": "accepted", "attachment": record}, status=201)


def _attachment_download_id(request_path: str) -> str | None:
    parts = [part for part in request_path.split("/") if part]
    if len(parts) == 4 and parts[:2] == ["api", "attachments"] and parts[3] == "download":
        return parts[2]
    return None


def _attachment_download_response(root_path: Path, attachment_id: str) -> ConsoleResponse:
    result = ui_state.read_attachment_blob(root_path, attachment_id)
    if result is None:
        return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")
    body, content_type, _filename = result
    return ConsoleResponse(200, content_type, body)


def _export_response(root_path: Path, fmt: str) -> ConsoleResponse:
    """Serialize the current state snapshot to a read-only download.

    Supported formats: ``board.csv``, ``taskset.md``, ``status.json``,
    ``backup.zip``. Export never mutates state.
    """

    state = ui_state.build_state(root_path)
    if fmt == "board.csv":
        body = ui_export.export_board_csv(state).encode("utf-8")
        return ConsoleResponse(200, "text/csv; charset=utf-8", body)
    if fmt == "taskset.md":
        body = ui_export.export_taskset_markdown(state).encode("utf-8")
        return ConsoleResponse(200, "text/markdown; charset=utf-8", body)
    if fmt == "status.json":
        body = ui_export.export_status_snapshot(state).encode("utf-8")
        return ConsoleResponse(200, "application/json; charset=utf-8", body)
    if fmt == "backup.zip":
        body = ui_export.export_backup_zip(state)
        return ConsoleResponse(200, "application/zip", body)
    return ConsoleResponse(404, "text/plain; charset=utf-8", b"unknown export format\n")


def _import_candidates_from_payload(payload: dict[str, object]) -> tuple[list[dict[str, object]], list[str]]:
    """Parse an upload payload (``format`` + ``content``) into candidates."""

    fmt = str(payload.get("format") or "").strip().lower()
    content = payload.get("content")
    if not isinstance(content, str):
        return [], ["content must be a string"]
    if fmt == "csv":
        return ui_export.parse_csv_import(content), []
    if fmt in {"md", "markdown"}:
        return ui_export.parse_markdown_import(content), []
    return [], [f"unsupported import format: {fmt!r} (expected csv or md)"]


def _import_preview_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    candidates, errors = _import_candidates_from_payload(payload)
    if errors:
        return _json_response({"status": "failed", "errors": errors}, status=400)
    state = ui_state.build_state(root_path)
    preview = ui_export.build_import_preview(candidates, state)
    return _json_response(preview, status=200)


def _import_commit_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    """Create task.create proposals for each non-duplicate candidate.

    Re-parses + re-checks server-side (never trusts the client's preview) and
    only emits a task.create command for candidates the server considers new
    and valid. Each command flows through ui_commands.submit_command, so the
    proposal/board-sync gate chain is the only writer.
    """

    candidates, errors = _import_candidates_from_payload(payload)
    if errors:
        return _json_response({"status": "failed", "errors": errors}, status=400)
    state = ui_state.build_state(root_path)
    preview = ui_export.build_import_preview(candidates, state)

    results: list[dict[str, object]] = []
    created = 0
    skipped = 0
    for item in preview["items"]:
        if item.get("action") != "create":
            skipped += 1
            results.append({"line": item.get("line"), "title": item.get("title"), "status": "skipped", "reason": item.get("duplicate_reasons") or item.get("errors")})
            continue
        create_payload = ui_export.candidate_to_task_create_payload(item)
        command_result = ui_commands.submit_command(root_path, {"type": "task.create", "payload": create_payload})
        if command_result.get("status") == "accepted":
            created += 1
        else:
            skipped += 1
        results.append({
            "line": item.get("line"),
            "title": item.get("title"),
            "status": command_result.get("status"),
            "command_id": command_result.get("id"),
            "errors": command_result.get("errors"),
        })
    summary = {
        "status": "accepted",
        "resource": "import_commit",
        "counts": {"created": created, "skipped": skipped, "total": len(preview["items"])},
        "results": results,
    }
    return _json_response(summary, status=202)


def build_response(path: str, root: Path | str, *, method: str = "GET", body: bytes | None = None) -> ConsoleResponse:
    """B-04: top-level guard around request dispatch. Any unexpected handler
    exception returns a clean 500 with a generic body (no internal detail leaked)
    and logs the full traceback to stderr — hardening WITHOUT masking, so one bad
    input can never silently reset the connection or dump a traceback to the
    client. Root-cause input validation (e.g. B-01) remains the first line of
    defense; this is defense-in-depth."""
    try:
        return _dispatch_response(path, root, method=method, body=body)
    except Exception:  # noqa: BLE001 - last-resort guard for ANY handler failure
        traceback.print_exc()
        return _json_response(
            {"status": "error", "error": "internal server error"}, status=500
        )


def _dispatch_response(path: str, root: Path | str, *, method: str = "GET", body: bytes | None = None) -> ConsoleResponse:
    root_path = Path(root)
    parsed_url = urlparse(path)
    request_path = parsed_url.path
    method = method.upper()
    if method in {"POST", "PATCH"}:
        payload, errors = _decode_json_body(body)
        if errors:
            return _json_response({"status": "failed", "errors": errors}, status=400)
        if method == "POST" and request_path == "/api/commands":
            return _command_response(root_path, payload)
        if method == "POST" and request_path == "/api/tasks":
            return _command_response(root_path, {"type": "task.create", "payload": payload})
        if method == "POST" and request_path == "/api/messages":
            return _command_response(root_path, {"type": "task.comment", "target": payload.get("task_id"), "payload": payload})
        # Import preview (TASK-AR-333): parse the uploaded payload and return a
        # duplicate-checked preview. This NEVER writes — preview only.
        if method == "POST" and request_path == "/api/import/preview":
            return _import_preview_response(root_path, payload)
        # Import commit (TASK-AR-333): turn each selected, non-duplicate
        # candidate into a task.create proposal via submit_command. No direct
        # task-file writes happen in the console.
        if method == "POST" and request_path == "/api/import/commit":
            return _import_commit_response(root_path, payload)
        task_match = re_api_task_route(request_path)
        if task_match and method == "PATCH":
            return _command_response(root_path, {"type": "task.update", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "reorder":
            return _command_response(root_path, {"type": "task.reorder", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "archive":
            return _command_response(root_path, {"type": "task.archive", "target": task_match[0], "payload": payload})
        # TASK-AR-332: file upload is the ONE legitimate file-write path. It is
        # NOT a ui_commands proposal: it validates/normalizes and writes the
        # bytes + an evidence sidecar under the attachments dir only.
        if method == "POST" and request_path == "/api/attachments":
            return _attachment_upload_response(root_path, payload)
        return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")

    if request_path in {"", "/"}:
        return ConsoleResponse(200, "text/html; charset=utf-8", _bytes(HTML))
    if request_path == "/favicon.ico":
        return ConsoleResponse(204, "image/x-icon", b"")
    if request_path == "/app.css":
        return ConsoleResponse(200, "text/css; charset=utf-8", _bytes(CSS))
    if request_path == "/app.js":
        return ConsoleResponse(200, "application/javascript; charset=utf-8", _bytes(JS))
    vendor_response = _vendor_asset_response(request_path)
    if vendor_response is not None:
        return vendor_response
    if request_path == "/api/state":
        return _json_response(ui_state.build_state(root_path))
    if request_path == "/api/inbox":
        # Decision-first cockpit data (TASK-AR-564): the 6-group attention inbox derived
        # from existing records by scripts/attention_inbox.py (stdlib, PyYAML-free).
        return _inbox_response(root_path)
    if request_path == "/api/stream":
        return _sse_response(ui_state.build_state(root_path))
    # On-demand knowledge-graph view (TASK-AR / #5): a degree-ranked bounded subgraph,
    # built lazily off the polled state because it scans work items, reviews, and git.
    if request_path == "/api/knowledge-graph":
        params = parse_qs(parsed_url.query)
        try:
            limit = int(params.get("limit", [""])[0])
        except (ValueError, IndexError):
            limit = ui_state.KNOWLEDGE_GRAPH_VIEW_LIMIT
        return _json_response(ui_state.build_knowledge_graph_view(root_path, limit=limit))
    if request_path == "/api/events":
        state = ui_state.build_state(root_path)
        filters = {key: values[0] for key, values in parse_qs(parsed_url.query).items() if values}
        return _json_response(
            {
                "generated_at": state["generated_at"],
                "resource": "events",
                "items": ui_state.filter_events(state["events"], filters),
                "sources": state["sources"],
                "gaps": state["gaps"],
                "warnings": state["warnings"],
            }
        )
    if request_path == "/api/replay/snapshot":
        state = ui_state.build_state(root_path)
        filters = {key: values[0] for key, values in parse_qs(parsed_url.query).items() if values}
        return _json_response(ui_state.build_replay_snapshot(state["replay"], filters.get("at")))
    download_id = _attachment_download_id(request_path)
    if download_id is not None:
        return _attachment_download_response(root_path, download_id)

    # Export routes (TASK-AR-333) are strictly read-only downloads: they
    # serialize the current ui_state snapshot to a portable format.
    if request_path.startswith("/api/export/"):
        return _export_response(root_path, request_path[len("/api/export/") :])

    if request_path == "/api/search":
        state = ui_state.build_state(root_path)
        params = parse_qs(parsed_url.query)
        query = (params.get("q", [""])[0] or "").strip()
        results = ui_state.run_search(state["search_index"], query) if query else []
        parsed_query = ui_state.parse_search_query(query)
        return _json_response(
            {
                "generated_at": state["generated_at"],
                "resource": "search",
                "query": query,
                "operators": parsed_query["operators"],
                "terms": parsed_query["terms"],
                "entity_types": list(ui_state.SEARCH_ENTITY_TYPES),
                "items": results,
                "total": len(results),
            }
        )
    # Unified entity catalog + command-palette search (TASK-AR-539/540). Reads the
    # generated ENTITY-CATALOG.json directly (manifest-first), NOT build_state, so
    # the palette stays instant. `?q=` (with optional `kind:`/`@` prefix) searches;
    # `?kind=` narrows; no query returns the full catalog + kind counts.
    if request_path == "/api/catalog":
        params = parse_qs(parsed_url.query)
        query = (params.get("q", [""])[0] or "").strip()
        kinds = [value for value in params.get("kind", []) if value]
        if query or kinds:
            items = ui_state.catalog_search(root_path, query, kinds=kinds or None)
            return _json_response(
                {"resource": "catalog_search", "query": query, "kinds": kinds, "items": items, "total": len(items)}
            )
        catalog = ui_state.load_catalog(root_path)
        return _json_response(
            {
                "resource": "catalog",
                "schema": catalog.get("schema"),
                "entity_count": catalog.get("entity_count", len(catalog.get("entities", []))),
                "kind_counts": catalog.get("kind_counts", {}),
                "entities": catalog.get("entities", []),
            }
        )
    # Entity detail + forward relations + computed backlinks (TASK-AR-541).
    if request_path == "/api/catalog/entity":
        entity_id = (parse_qs(parsed_url.query).get("id", [""])[0] or "").strip()
        detail = ui_state.catalog_entity(root_path, entity_id)
        if detail is None:
            return _json_response({"resource": "catalog_entity", "id": entity_id, "error": "not found"}, status=404)
        return _json_response({"resource": "catalog_entity", **detail})
    # Faceted counts + needs-attention rollup (TASK-AR-543).
    if request_path == "/api/catalog/facets":
        return _json_response({"resource": "catalog_facets", **ui_state.catalog_facets(root_path)})
    # Governance/knowledge document surface (TASK-AR-545).
    if request_path == "/api/catalog/docs":
        return _json_response({"resource": "catalog_docs", **ui_state.catalog_docs(root_path)})
    # Activity/provenance timeline for an entity (TASK-AR-542).
    if request_path == "/api/activity":
        entity_id = (parse_qs(parsed_url.query).get("id", [""])[0] or "").strip()
        return _json_response({"resource": "activity", **ui_state.entity_activity(root_path, entity_id)})
    # Live SCM surface: branches + recent commits (TASK-AR-544).
    if request_path == "/api/scm":
        return _json_response({"resource": "scm", **ui_state.scm_overview(root_path)})

    api_resources = {
        "/api/tasks": "tasks",
        "/api/agents": "agents",
        "/api/task-sets": "task_sets",
        "/api/task_sets": "task_sets",
        "/api/messages": "messages",
        "/api/goals": "goals",
        "/api/inflight": "inflight",
        "/api/work_explorer": "work_explorer",
        "/api/work-explorer": "work_explorer",
        "/api/work_state": "work_state",
        "/api/work-state": "work_state",
        "/api/meeting_room": "meeting_room",
        "/api/meeting-room": "meeting_room",
        "/api/tasksets_board": "tasksets_board",
        "/api/tasksets-board": "tasksets_board",
        "/api/taskset_completion": "taskset_completion",
        "/api/taskset-completion": "taskset_completion",
        "/api/team_agents": "team_agents",
        "/api/team-agents": "team_agents",
        "/api/teams": "teams",
        "/api/growth": "growth",
        "/api/workload": "workload",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/attachments": "attachments",
        "/api/replay": "replay",
        "/api/graph": "graph",
        "/api/live_map": "live_map",
        "/api/live-map": "live_map",
        "/api/office_map": "office_map",
        "/api/office-map": "office_map",
        "/api/org_chart": "org_chart",
        "/api/org-chart": "org_chart",
        "/api/state-machines": "state_machines",
        "/api/roadmap": "roadmap",
        "/api/roadmap-timeline": "roadmap_timeline",
        "/api/roadmap_timeline": "roadmap_timeline",
        "/api/planning": "planning",
        "/api/custom_properties": "custom_properties",
        "/api/custom-properties": "custom_properties",
        "/api/labels": "labels",
        "/api/automation_rules": "automation_rules",
        "/api/automation-rules": "automation_rules",
        "/api/triage": "triage",
        "/api/reviews": "reviews",
        "/api/schedules": "schedules",
        "/api/calendar": "calendar",
        "/api/notifications": "notifications",
        "/api/daily_brief": "daily_brief",
        "/api/daily-brief": "daily_brief",
        "/api/notification_routing": "notification_routing",
        "/api/notification-routing": "notification_routing",
        "/api/workspaces": "workspaces",
        "/api/widgets": "widgets",
        "/api/i18n": "i18n",
        "/api/search_index": "search_index",
        "/api/search-index": "search_index",
        "/api/commands": "commands",
    }
    if request_path in api_resources:
        return _json_response(ui_state.build_resource(root_path, api_resources[request_path]))
    return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")


def re_api_task_route(request_path: str) -> tuple[str, str | None] | None:
    parts = [part for part in request_path.split("/") if part]
    if len(parts) == 3 and parts[:2] == ["api", "tasks"]:
        return parts[2], None
    if len(parts) == 4 and parts[:2] == ["api", "tasks"]:
        return parts[2], parts[3]
    return None


class _ConsoleHandler(BaseHTTPRequestHandler):
    root: Path = Path.cwd()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length else b""

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root, method="POST", body=self._read_body())
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def do_PATCH(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root, method="PATCH", body=self._read_body())
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(root: Path, *, host: str = "127.0.0.1", port: int = 8765) -> int:
    root_path = Path(root).resolve()
    handler = type("AgentRuntimeConsoleHandler", (_ConsoleHandler,), {"root": root_path})
    # Pre-warm the state cache off-thread so the FIRST browser request hits the
    # cache (~0.3s) instead of paying the cold build (~40s on a large store).
    threading.Thread(
        target=lambda: ui_state.build_state(root_path),
        daemon=True,
        name="console-state-warmup",
    ).start()
    with ThreadingHTTPServer((host, port), handler) as server:
        actual_host, actual_port = server.server_address[:2]
        print(f"Agent Runtime Console: http://{actual_host}:{actual_port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Agent Runtime Console stopped.")
    return 0
