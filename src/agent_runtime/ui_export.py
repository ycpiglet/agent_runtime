"""Import/export engine for the runtime console (TASK-AR-333).

Export is strictly read-only: it serializes the in-memory ``ui_state`` snapshot
to standard, portable formats (Markdown package, board CSV, status JSON
snapshot, and a full backup zip bundle). Nothing here touches task files.

Import is proposal-only. It *parses* an uploaded Markdown checklist or CSV into
normalized task-create candidates, attaches a preview with duplicate detection
against the live state, and hands the candidates back. The console then turns
each non-duplicate candidate into a ``task.create`` command via
``ui_commands.submit_command`` -> ``.ui_outbox`` proposal. This module never
writes a task file directly.

The CSV columns are a stable contract so an exported board round-trips through
import with no loss:

    id, display_id, title, status, priority, owner, task_set_id, order, labels,
    blocked_by, blocks, due, description

CSV cells are quoted per RFC 4180 and de-fanged against spreadsheet/CSV
injection: any cell whose first character is one of ``= + - @`` (or a leading
tab / CR that some parsers strip to expose those) is prefixed with a single
quote so it cannot be interpreted as a formula on re-open.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Any, Iterable

# Stable export/import column contract. Order is the canonical CSV header order
# and is what guarantees a lossless round-trip.
BOARD_COLUMNS: tuple[str, ...] = (
    "id",
    "display_id",
    "title",
    "status",
    "priority",
    "owner",
    "task_set_id",
    "order",
    "labels",
    "blocked_by",
    "blocks",
    "due",
    "description",
)

# List-valued columns are joined/split on this separator so a single CSV cell
# round-trips a list without colliding with the CSV comma delimiter.
_LIST_SEP = "; "
_LIST_SPLIT = re.compile(r"\s*;\s*")

# Characters that make a spreadsheet treat a cell as a formula. A leading one of
# these (after stripping whitespace control chars some apps trim) is dangerous.
_CSV_INJECTION_PREFIXES = ("=", "+", "-", "@")
_CSV_INJECTION_LEADING_STRIP = ("\t", "\r", "\n", " ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# CSV-injection hardening
# --------------------------------------------------------------------------- #
def sanitize_csv_cell(value: Any) -> str:
    """Return ``value`` as a string safe to drop into a CSV/spreadsheet cell.

    If the (leading-whitespace-stripped) cell begins with a formula trigger
    (``= + - @``) we prefix a single quote so the value is preserved as text and
    never executed as a formula. The ``csv`` module still handles quoting of
    commas/quotes/newlines on top of this.
    """

    text = "" if value is None else str(value)
    probe = text
    while probe and probe[0] in _CSV_INJECTION_LEADING_STRIP:
        probe = probe[1:]
    if probe and probe[0] in _CSV_INJECTION_PREFIXES:
        return "'" + text
    return text


def _unsanitize_csv_cell(value: str) -> str:
    """Inverse of :func:`sanitize_csv_cell` for round-trip import.

    A leading single quote that guards a formula trigger is stripped so the
    original text is recovered. A lone leading quote in front of a normal value
    is left intact (we only strip when it was clearly an injection guard).
    """

    if value.startswith("'"):
        rest = value[1:]
        probe = rest
        while probe and probe[0] in _CSV_INJECTION_LEADING_STRIP:
            probe = probe[1:]
        if probe and probe[0] in _CSV_INJECTION_PREFIXES:
            return rest
    return value


# --------------------------------------------------------------------------- #
# Field projection
# --------------------------------------------------------------------------- #
def _task_owner(task: dict[str, Any]) -> str:
    return str(task.get("owner_agent") or task.get("owner") or "")


def _join_list(value: Any) -> str:
    if isinstance(value, list):
        return _LIST_SEP.join(str(item) for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value)


def _split_list(value: str) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    return [part for part in _LIST_SPLIT.split(text) if part]


def _task_to_row(task: dict[str, Any]) -> dict[str, str]:
    """Project a state ``task`` dict onto the stable export column set."""

    return {
        "id": str(task.get("id") or ""),
        "display_id": str(task.get("display_id") or task.get("id") or ""),
        "title": str(task.get("title") or ""),
        "status": str(task.get("status") or ""),
        "priority": str(task.get("priority") or ""),
        "owner": _task_owner(task),
        "task_set_id": str(task.get("task_set_id") or ""),
        "order": str(task.get("order") if task.get("order") is not None else ""),
        "labels": _join_list(task.get("labels")),
        "blocked_by": _join_list(task.get("blocked_by")),
        "blocks": _join_list(task.get("blocks")),
        "due": str(task.get("due") or ""),
        "description": str(task.get("description") or ""),
    }


# --------------------------------------------------------------------------- #
# Export: board -> CSV
# --------------------------------------------------------------------------- #
def export_board_csv(state: dict[str, Any]) -> str:
    """Serialize the task board to RFC-4180 CSV with injection-safe cells."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(BOARD_COLUMNS)
    for task in state.get("tasks", []):
        row = _task_to_row(task)
        writer.writerow([sanitize_csv_cell(row[col]) for col in BOARD_COLUMNS])
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# Export: taskset -> Markdown package
# --------------------------------------------------------------------------- #
def _md_escape(value: Any) -> str:
    """Escape a value for safe inline-Markdown rendering.

    Pipes (table breakers) and the leading markup chars that could let injected
    content restructure the document are neutralized. Newlines collapse to a
    space so a single field cannot inject extra rows.
    """

    text = "" if value is None else str(value)
    text = text.replace("\\", "\\\\")
    text = text.replace("|", "\\|")
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return text


def export_taskset_markdown(state: dict[str, Any]) -> str:
    """Render every taskset (and its tasks) as a Markdown package document."""

    tasks = state.get("tasks", [])
    by_set: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        key = str(task.get("task_set_id") or "(unassigned)")
        by_set.setdefault(key, []).append(task)

    set_titles: dict[str, str] = {}
    for ts in state.get("task_sets", []):
        ts_id = str(ts.get("id") or "")
        if ts_id:
            set_titles[ts_id] = str(ts.get("display_name") or ts.get("title") or ts_id)

    lines: list[str] = [
        "# Taskset Export Package",
        "",
        f"- generated_at: {_md_escape(state.get('generated_at') or _now_iso())}",
        f"- tasksets: {len(by_set)}",
        f"- tasks: {len(tasks)}",
        "",
    ]
    for set_id in sorted(by_set):
        title = set_titles.get(set_id, set_id)
        lines.append(f"## {_md_escape(title)} ({_md_escape(set_id)})")
        lines.append("")
        for task in by_set[set_id]:
            status = str(task.get("status") or "").lower()
            checked = "x" if status in {"completed", "done", "closed"} else " "
            tid = _md_escape(task.get("display_id") or task.get("id"))
            ttitle = _md_escape(task.get("title"))
            meta_bits = []
            if task.get("status"):
                meta_bits.append(f"status={_md_escape(task.get('status'))}")
            if task.get("priority"):
                meta_bits.append(f"priority={_md_escape(task.get('priority'))}")
            if _task_owner(task):
                meta_bits.append(f"owner={_md_escape(_task_owner(task))}")
            suffix = f" ({', '.join(meta_bits)})" if meta_bits else ""
            lines.append(f"- [{checked}] **{tid}** {ttitle}{suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Export: status snapshot -> JSON
# --------------------------------------------------------------------------- #
def export_status_snapshot(state: dict[str, Any]) -> str:
    """Serialize a compact status snapshot (counts + per-task status) to JSON."""

    tasks = state.get("tasks", [])
    status_counts: dict[str, int] = {}
    lane_counts: dict[str, int] = {}
    for task in tasks:
        status = str(task.get("status") or "unknown")
        lane = str(task.get("lane") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
    snapshot = {
        "generated_at": state.get("generated_at") or _now_iso(),
        "resource": "status_snapshot",
        "totals": {
            "tasks": len(tasks),
            "task_sets": len(state.get("task_sets", [])),
            "agents": len(state.get("agents", [])),
        },
        "status_counts": status_counts,
        "lane_counts": lane_counts,
        "tasks": [
            {
                "id": task.get("id"),
                "status": task.get("status"),
                "lane": task.get("lane"),
                "task_set_id": task.get("task_set_id"),
                "priority": task.get("priority"),
                "owner": _task_owner(task),
            }
            for task in tasks
        ],
    }
    return json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"


# --------------------------------------------------------------------------- #
# Export: full backup -> zip bundle
# --------------------------------------------------------------------------- #
# Members of the backup bundle. Kept stable so importers can rely on layout.
BACKUP_MEMBERS: tuple[str, ...] = (
    "manifest.json",
    "board.csv",
    "taskset.md",
    "status.json",
    "state.json",
)


def export_backup_zip(state: dict[str, Any]) -> bytes:
    """Bundle every export artifact into a single deterministic zip archive."""

    generated_at = state.get("generated_at") or _now_iso()
    manifest = {
        "kind": "agent-runtime-backup",
        "version": 1,
        "generated_at": generated_at,
        "members": list(BACKUP_MEMBERS),
        "totals": {
            "tasks": len(state.get("tasks", [])),
            "task_sets": len(state.get("task_sets", [])),
        },
    }
    members: dict[str, bytes] = {
        "manifest.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        "board.csv": export_board_csv(state).encode("utf-8"),
        "taskset.md": export_taskset_markdown(state).encode("utf-8"),
        "status.json": export_status_snapshot(state).encode("utf-8"),
        "state.json": (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    buffer = io.BytesIO()
    # Fixed timestamp + stable member order => byte-deterministic archive.
    fixed_time = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in BACKUP_MEMBERS:
            info = zipfile.ZipInfo(name, date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, members[name])
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# Import: parse CSV / Markdown -> normalized candidates
# --------------------------------------------------------------------------- #
_VALID_STATUSES = {
    "planned",
    "in_progress",
    "review",
    "blocked",
    "completed",
    "done",
    "closed",
}
_VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def _normalize_candidate(raw: dict[str, Any], *, line: int) -> dict[str, Any]:
    """Coerce a parsed row into a normalized task-create candidate."""

    title = str(raw.get("title") or "").strip()
    candidate: dict[str, Any] = {
        "line": line,
        "id": str(raw.get("id") or "").strip(),
        "title": title,
        "status": str(raw.get("status") or "").strip(),
        "priority": str(raw.get("priority") or "").strip(),
        "owner": str(raw.get("owner") or "").strip(),
        "task_set_id": str(raw.get("task_set_id") or "").strip(),
        "order": str(raw.get("order") or "").strip(),
        "labels": _split_list(str(raw.get("labels") or "")),
        "blocked_by": _split_list(str(raw.get("blocked_by") or "")),
        "blocks": _split_list(str(raw.get("blocks") or "")),
        "due": str(raw.get("due") or "").strip(),
        "description": str(raw.get("description") or "").strip(),
    }
    errors: list[str] = []
    if not candidate["title"]:
        errors.append("missing title")
    if candidate["id"] and not re.fullmatch(r"TASK-[A-Za-z0-9-]+", candidate["id"]):
        errors.append(f"invalid id: {candidate['id']!r}")
    if candidate["status"] and candidate["status"] not in _VALID_STATUSES:
        errors.append(f"invalid status: {candidate['status']!r}")
    if candidate["priority"] and candidate["priority"] not in _VALID_PRIORITIES:
        errors.append(f"invalid priority: {candidate['priority']!r}")
    candidate["errors"] = errors
    return candidate


def parse_csv_import(text: str) -> list[dict[str, Any]]:
    """Parse an exported (or external) CSV into normalized candidates."""

    reader = csv.DictReader(io.StringIO(text))
    candidates: list[dict[str, Any]] = []
    for index, row in enumerate(reader, start=2):  # row 1 is the header
        cleaned = {
            (key or "").strip(): _unsanitize_csv_cell(str(value or ""))
            for key, value in row.items()
            if key is not None
        }
        # Skip wholly empty rows so a trailing newline never yields a phantom.
        if not any(v.strip() for v in cleaned.values()):
            continue
        candidates.append(_normalize_candidate(cleaned, line=index))
    return candidates


_MD_CHECKLIST = re.compile(
    r"^\s*[-*]\s*\[(?P<check>[ xX])\]\s*(?P<rest>.+?)\s*$",
)
_MD_BOLD_ID = re.compile(r"\*\*(?P<id>TASK-[A-Za-z0-9-]+)\*\*\s*(?P<title>.*)")
_MD_META = re.compile(r"\((?P<meta>[^()]*=[^()]*)\)\s*$")


def parse_markdown_import(text: str) -> list[dict[str, Any]]:
    """Parse a Markdown checklist into normalized candidates.

    Accepts the package format we export (``- [ ] **TASK-X** title (k=v, ...)``)
    as well as bare checklist lines (``- [ ] some title``).
    """

    candidates: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        match = _MD_CHECKLIST.match(raw_line)
        if not match:
            continue
        checked = match.group("check").lower() == "x"
        rest = match.group("rest").strip()

        raw: dict[str, Any] = {}
        meta_match = _MD_META.search(rest)
        if meta_match:
            for pair in meta_match.group("meta").split(","):
                key, _, value = pair.partition("=")
                key = key.strip()
                value = value.strip()
                if key:
                    raw[key] = value
            rest = rest[: meta_match.start()].strip()

        bold = _MD_BOLD_ID.search(rest)
        if bold:
            raw["id"] = bold.group("id")
            raw["title"] = bold.group("title").strip()
        else:
            raw["title"] = rest

        if "status" not in raw:
            raw["status"] = "completed" if checked else "planned"
        candidates.append(_normalize_candidate(raw, line=index))
    return candidates


# --------------------------------------------------------------------------- #
# Import: preview + duplicate detection
# --------------------------------------------------------------------------- #
def _existing_index(state: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Build lookup sets of existing task ids and normalized titles."""

    ids: set[str] = set()
    titles: set[str] = set()
    for task in state.get("tasks", []):
        tid = str(task.get("id") or "").strip()
        if tid:
            ids.add(tid)
        title = str(task.get("title") or "").strip().casefold()
        if title:
            titles.add(title)
    return ids, titles


def build_import_preview(
    candidates: Iterable[dict[str, Any]],
    state: dict[str, Any],
) -> dict[str, Any]:
    """Annotate candidates with duplicate/validity flags for a preview.

    A candidate is a duplicate when its explicit id matches an existing task id,
    or (when it has no id) when its normalized title matches an existing task
    title. Duplicates within the upload itself are also flagged. Nothing is
    written here -- this is purely advisory for the UI preview step.
    """

    existing_ids, existing_titles = _existing_index(state)
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    items: list[dict[str, Any]] = []
    counts = {"total": 0, "new": 0, "duplicate": 0, "invalid": 0}

    for candidate in candidates:
        counts["total"] += 1
        item = dict(candidate)
        reasons: list[str] = []
        cid = str(item.get("id") or "").strip()
        ctitle = str(item.get("title") or "").strip().casefold()

        if cid and cid in existing_ids:
            reasons.append(f"id exists in board: {cid}")
        if cid and cid in seen_ids:
            reasons.append(f"duplicate id in upload: {cid}")
        if not cid and ctitle and ctitle in existing_titles:
            reasons.append("title exists in board")
        if not cid and ctitle and ctitle in seen_titles:
            reasons.append("duplicate title in upload")

        invalid = bool(item.get("errors"))
        duplicate = bool(reasons)
        item["duplicate"] = duplicate
        item["duplicate_reasons"] = reasons
        if invalid:
            item["action"] = "skip"
            counts["invalid"] += 1
        elif duplicate:
            item["action"] = "skip"
            counts["duplicate"] += 1
        else:
            item["action"] = "create"
            counts["new"] += 1

        if cid:
            seen_ids.add(cid)
        if ctitle:
            seen_titles.add(ctitle)
        items.append(item)

    return {
        "generated_at": _now_iso(),
        "resource": "import_preview",
        "counts": counts,
        "items": items,
    }


def candidate_to_task_create_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    """Build a ``task.create`` payload from a normalized candidate.

    Only known, safe fields are forwarded; this payload is handed to
    ``ui_commands.submit_command`` which performs the proposal write.
    """

    payload: dict[str, Any] = {"title": candidate.get("title") or ""}
    for key in ("id", "status", "priority", "owner", "task_set_id", "due", "description"):
        value = candidate.get(key)
        if value:
            payload[key] = value
    order = str(candidate.get("order") or "").strip()
    if order:
        try:
            payload["order"] = int(order)
        except ValueError:
            pass
    labels = candidate.get("labels")
    if isinstance(labels, list) and labels:
        payload["tags"] = list(labels)
    return payload
