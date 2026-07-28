from __future__ import annotations

"""Bounded, privacy-safe state summaries for Scribe continuity checks.

Canonical host state remains host-owned.  This module only reads configured or
conventional Markdown/JSON sources and, when explicitly requested, writes one
generated projection with derived metadata and bounded selected items.
"""

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import config as _config

PROJECTION_SCHEMA = "agent-runtime-scribe-projection/v1"
EVALUATION_SCHEMA = "agent-runtime-scribe-evaluation/v1"
DEFAULT_PROJECTION_PATH = _config.DEFAULT_STATE_PROJECTION
CONVENTIONAL_SOURCE_PATHS = (
    "agents/lead_engineer/STATUS.md",
    "STATUS.md",
    "BACKLOG.md",
    "docs/PROJECT_STATUS.md",
    "docs/PROJECT_STATUS.ko.md",
    "PROJECT_STATUS.md",
)

MAX_SOURCES = 8
MAX_SELECTED_ITEMS = 10
MAX_HEADING_CHARS = 160
MAX_ITEM_CHARS = 240
MAX_PROJECTION_BYTES = 32 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
DUE_AT = 13
OVERDUE_AT = 16

_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-+*]\s+(.+?)\s*$")
_CHECKBOX_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")
_ENV_ASSIGNMENT_RE = re.compile(r"(?:^|\s)[A-Za-z_][A-Za-z0-9_]*\s*=")
_PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE)
_CONTENT_FIELD_RE = re.compile(
    r"^\s*(?:prompt|system_prompt|transcript|conversation|messages?|raw_body|body|content)\s*[:=]",
    re.IGNORECASE,
)
_PROMPT_TRANSCRIPT_RE = re.compile(r"\b(?:prompt|transcript)\b", re.IGNORECASE)
_SECRET_VALUE_RE = re.compile(
    r"\b(api(?:[_\s-]?key)|secret|token|password|passwd|credential|authorization|cookie)"
    r"\b\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)
_CREDENTIAL_PATTERNS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
)
_JSON_LIST_KEYS = ("items", "entries", "tasks", "work", "backlog")
_JSON_VALUE_KEYS = ("id", "name", "title", "summary", "status")
_COLD_JSON_STATUSES = {
    "cancelled",
    "canceled",
    "closed",
    "complete",
    "completed",
    "done",
    "resolved",
}


class StateProjectionError(ValueError):
    """Raised when a state source or projection target is unsafe."""


@dataclass(frozen=True)
class StateSource:
    adapter: str
    path: str
    configured: bool


@dataclass(frozen=True)
class StateSettings:
    sources: tuple[StateSource, ...]
    projection_path: str
    configured: bool
    findings: tuple[dict[str, str], ...] = ()


def classify_hot_count(count: int) -> str:
    if count >= OVERDUE_AT:
        return "overdue"
    if count >= DUE_AT:
        return "due"
    return "ok"


def _finding(
    code: str,
    *,
    path: str,
    detail: str,
    severity: str = "warning",
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "path": path,
        "detail": detail,
    }


def _bounded(value: object, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def redact_text(value: object, *, limit: int) -> str:
    """Return one bounded derived string without credential or raw-context data."""

    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    if (
        _PRIVATE_KEY_RE.search(text)
        or _CONTENT_FIELD_RE.search(text)
        or _PROMPT_TRANSCRIPT_RE.search(text)
        or _ENV_ASSIGNMENT_RE.search(text)
    ):
        return "[REDACTED]"
    text = _SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}: [REDACTED]", text)
    for pattern in _CREDENTIAL_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return _bounded(text, limit)


def _strip_heading_suffix(value: str) -> str:
    return re.sub(r"\s+#+\s*$", "", value).strip()


def parse_markdown(text: str) -> dict[str, Any]:
    """Derive headings and list items without retaining the source body."""

    headings: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    total_count = 0
    hot_count = 0
    cold_count = 0
    nearest_heading = ""

    for index, line in enumerate(text.splitlines()):
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            heading = redact_text(
                _strip_heading_suffix(heading_match.group(2)),
                limit=MAX_HEADING_CHARS,
            )
            if heading:
                nearest_heading = heading
                headings.append(
                    {
                        "heading": heading,
                        "level": len(heading_match.group(1)),
                        "source_order": index,
                    }
                )
            continue

        bullet_match = _BULLET_RE.match(line)
        if not bullet_match:
            continue
        total_count += 1
        raw_item = bullet_match.group(1)
        checkbox_match = _CHECKBOX_RE.match(raw_item)
        if checkbox_match:
            checked = checkbox_match.group(1).lower() == "x"
            item = redact_text(checkbox_match.group(2), limit=MAX_ITEM_CHARS)
            if checked:
                cold_count += 1
                continue
            hot_count += 1
            candidates.append(
                {
                    "heading": nearest_heading,
                    "item": item or "[REDACTED]",
                    "checklist": "unchecked",
                    "source_order": index,
                    "_priority": 0,
                }
            )
            continue

        hot_count += 1
        item = redact_text(raw_item, limit=MAX_ITEM_CHARS)
        candidates.append(
            {
                "heading": nearest_heading,
                "item": item or "[REDACTED]",
                "checklist": "none",
                "source_order": index,
                "_priority": 1,
            }
        )

    if total_count == 0:
        total_count = len(headings)
        hot_count = len(headings)
        candidates = [
            {
                "heading": heading["heading"],
                "item": heading["heading"],
                "checklist": "heading",
                "source_order": heading["source_order"],
                "_priority": 2,
            }
            for heading in headings
        ]

    candidates.sort(key=lambda item: (item["_priority"], item["source_order"]))
    return {
        "total_count": total_count,
        "hot_count": hot_count,
        "cold_count": cold_count,
        "candidates": candidates,
    }


def _json_entries(payload: object) -> list[object] | None:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None
    for key in _JSON_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return None


def _json_item(entry: object) -> tuple[str, str]:
    if isinstance(entry, str):
        return redact_text(entry, limit=MAX_ITEM_CHARS), ""
    if not isinstance(entry, dict):
        return "", ""
    values: list[str] = []
    status = ""
    for key in _JSON_VALUE_KEYS:
        value = entry.get(key)
        if not isinstance(value, (str, int, float, bool)) or value in ("", None):
            continue
        safe = redact_text(value, limit=MAX_ITEM_CHARS)
        if not safe:
            continue
        if key == "status":
            status = safe
            values.append(f"status {safe}")
        else:
            values.append(safe)
    return _bounded(" · ".join(values), MAX_ITEM_CHARS), status


def parse_json(text: str) -> dict[str, Any]:
    """Derive only allowlisted scalar fields from one bounded collection."""

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StateProjectionError(f"invalid JSON state source: {exc.msg}") from exc
    entries = _json_entries(payload)
    if entries is None:
        raise StateProjectionError(
            "JSON state source must be a top-level list or contain a list-valued "
            + "/".join(_JSON_LIST_KEYS)
        )

    candidates: list[dict[str, Any]] = []
    hot_count = 0
    cold_count = 0
    for index, entry in enumerate(entries):
        item, status = _json_item(entry)
        cold = status.strip().lower() in _COLD_JSON_STATUSES
        if cold:
            cold_count += 1
            continue
        hot_count += 1
        if not item:
            continue
        candidates.append(
            {
                "heading": "",
                "item": item,
                "checklist": "none",
                "source_order": index,
                "_priority": 1,
            }
        )
    return {
        "total_count": len(entries),
        "hot_count": hot_count,
        "cold_count": cold_count,
        "candidates": candidates,
    }


def _is_inside(root: Path, path: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _safe_target(root: Path, relative: str) -> Path:
    path = root / relative
    if not _is_inside(root, path):
        raise StateProjectionError(f"path resolves outside host root: {relative}")
    return path


def _symlink_ancestor(root: Path, target: Path) -> Path | None:
    current = target
    while current != root:
        if current.is_symlink():
            return current
        current = current.parent
    return None


def _config_is_present(root: Path) -> bool:
    return (root / _config.CONFIG_FILE).exists() or (
        root / _config.LEGACY_CONFIG_FILE
    ).exists()


def resolve_settings(
    root: Path,
    *,
    config: _config.AgentRuntimeConfig | None = None,
) -> StateSettings:
    root = root.resolve()
    findings: list[dict[str, str]] = []
    cfg = config
    configured = cfg is not None
    if cfg is None and _config_is_present(root):
        configured = True
        try:
            cfg = _config.load_config(root)
        except Exception as exc:
            findings.append(
                _finding(
                    "config-invalid",
                    path=_config.CONFIG_FILE,
                    detail=str(exc),
                )
            )
            return StateSettings(
                sources=(),
                projection_path=DEFAULT_PROJECTION_PATH,
                configured=True,
                findings=tuple(findings),
            )

    if cfg is not None and cfg.state_adapters:
        sources = tuple(
            StateSource(adapter=label, path=path, configured=True)
            for label, path in cfg.state_adapters[:MAX_SOURCES]
        )
        return StateSettings(
            sources=sources,
            projection_path=cfg.state_projection,
            configured=True,
            findings=tuple(findings),
        )

    projection_path = (
        cfg.state_projection if cfg is not None else DEFAULT_PROJECTION_PATH
    )
    for relative in CONVENTIONAL_SOURCE_PATHS:
        try:
            candidate = _safe_target(root, relative)
        except StateProjectionError:
            continue
        if candidate.is_file():
            return StateSettings(
                sources=(
                    StateSource(
                        adapter="conventional",
                        path=relative,
                        configured=False,
                    ),
                ),
                projection_path=projection_path,
                configured=configured,
                findings=tuple(findings),
            )

    findings.append(
        _finding(
            "source-unavailable",
            path=".",
            detail="no configured adapter or conventional state source is available",
        )
    )
    return StateSettings(
        sources=(),
        projection_path=projection_path,
        configured=configured,
        findings=tuple(findings),
    )


def _source_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _source_file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evaluate_source(root: Path, source: StateSource) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    base = {
        "adapter": source.adapter,
        "path": source.path,
        "configured": source.configured,
        "present": False,
        "digest": None,
        "total_count": None,
        "hot_count": None,
        "cold_count": None,
        "state": "unavailable",
        "selected_count": 0,
        "selected_items": [],
        "finding_codes": [],
    }
    try:
        path = _safe_target(root, source.path)
    except StateProjectionError as exc:
        finding = _finding("source-unsafe", path=source.path, detail=str(exc))
        findings.append(finding)
        base["finding_codes"] = [finding["code"]]
        return base, findings, []
    if not path.is_file():
        code = "source-missing" if source.configured else "source-unavailable"
        finding = _finding(
            code,
            path=source.path,
            detail="configured state source is missing"
            if source.configured
            else "conventional state source is unavailable",
        )
        findings.append(finding)
        base["finding_codes"] = [finding["code"]]
        return base, findings, []
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            base.update(present=True, digest=_source_file_digest(path))
            finding = _finding(
                "source-too-large",
                path=source.path,
                detail=f"source exceeds the {MAX_SOURCE_BYTES}-byte parse limit",
            )
            findings.append(finding)
            base["finding_codes"] = [finding["code"]]
            return base, findings, []
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        parsed = parse_json(text) if path.suffix.lower() == ".json" else parse_markdown(text)
    except (OSError, UnicodeError, StateProjectionError) as exc:
        finding = _finding("source-parse-error", path=source.path, detail=str(exc))
        findings.append(finding)
        base["present"] = True
        try:
            base["digest"] = _source_file_digest(path)
        except OSError:
            pass
        base["finding_codes"] = [finding["code"]]
        return base, findings, []

    base.update(
        present=True,
        digest=_source_digest(raw),
        total_count=parsed["total_count"],
        hot_count=parsed["hot_count"],
        cold_count=parsed["cold_count"],
        state=classify_hot_count(parsed["hot_count"]),
    )
    return base, findings, list(parsed["candidates"])


def _fingerprints(sources: Iterable[dict[str, Any]]) -> list[tuple[str, str, bool, str | None]]:
    fingerprints: list[tuple[str, str, bool, str | None]] = []
    for source in sources:
        present = source.get("present") is True
        fingerprints.append(
            (
                str(source.get("adapter") or ""),
                str(source.get("path") or ""),
                present,
                str(source.get("digest")) if present and source.get("digest") else None,
            )
        )
    return fingerprints


def _projection_status(
    root: Path,
    projection_path: str,
    sources: list[dict[str, Any]],
) -> tuple[str, list[dict[str, str]], dict[str, Any] | None]:
    findings: list[dict[str, str]] = []
    try:
        path = _safe_target(root, projection_path)
    except StateProjectionError as exc:
        return (
            "stale",
            [_finding("projection-unsafe", path=projection_path, detail=str(exc))],
            None,
        )
    if not path.is_file():
        return (
            "missing",
            [
                _finding(
                    "projection-missing",
                    path=projection_path,
                    detail="generated scribe projection is missing",
                )
            ],
            None,
        )
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_PROJECTION_BYTES:
            raise StateProjectionError(
                f"projection exceeds the {MAX_PROJECTION_BYTES}-byte limit"
            )
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != PROJECTION_SCHEMA:
            raise StateProjectionError(f"projection must declare schema {PROJECTION_SCHEMA}")
        if payload.get("projection_path") != projection_path:
            raise StateProjectionError("projection path metadata does not match configuration")
        projected_sources = payload.get("sources")
        if not isinstance(projected_sources, list):
            raise StateProjectionError("projection sources must be a list")
        if _fingerprints(projected_sources) != _fingerprints(sources):
            raise StateProjectionError("projection source paths or digests are stale")
    except (OSError, UnicodeError, json.JSONDecodeError, StateProjectionError) as exc:
        findings.append(
            _finding(
                "projection-stale",
                path=projection_path,
                detail=str(exc),
            )
        )
        return "stale", findings, None

    findings.append(
        _finding(
            "projection-fresh",
            path=projection_path,
            detail="all present source paths and SHA-256 digests match",
            severity="info",
        )
    )
    return "fresh", findings, payload


def _overall_state(sources: list[dict[str, Any]]) -> str:
    states = {str(source.get("state") or "unavailable") for source in sources}
    if "overdue" in states:
        return "overdue"
    if "due" in states:
        return "due"
    if "unavailable" in states or not states:
        return "unavailable"
    return "ok"


def evaluate_state(
    root: Path,
    *,
    config: _config.AgentRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Read current sources and projection metadata without writing anything."""

    root = root.resolve()
    settings = resolve_settings(root, config=config)
    findings = list(settings.findings)
    sources: list[dict[str, Any]] = []
    source_candidates: list[list[dict[str, Any]]] = []
    for source in settings.sources:
        evaluated, source_findings, candidates = _evaluate_source(root, source)
        sources.append(evaluated)
        source_candidates.append(candidates)
        findings.extend(source_findings)

    remaining = MAX_SELECTED_ITEMS
    selected_items: list[dict[str, Any]] = []
    for source, candidates in zip(sources, source_candidates):
        selected: list[dict[str, Any]] = []
        for candidate in candidates[:remaining]:
            clean = {
                "heading": candidate["heading"],
                "item": candidate["item"],
                "checklist": candidate["checklist"],
            }
            selected.append(clean)
            selected_items.append(
                {
                    "adapter": source["adapter"],
                    "path": source["path"],
                    **clean,
                }
            )
        source["selected_items"] = selected
        source["selected_count"] = len(selected)
        remaining -= len(selected)
        if remaining <= 0:
            remaining = 0

    state = _overall_state(sources)
    if state == "overdue":
        findings.append(
            _finding(
                "scribe-overdue",
                path=".",
                detail="at least one present source has 16 or more hot items",
            )
        )
    elif state == "due":
        findings.append(
            _finding(
                "scribe-due",
                path=".",
                detail="at least one present source has 13 to 15 hot items",
            )
        )
    elif state == "ok":
        findings.append(
            _finding(
                "scribe-ok",
                path=".",
                detail="all available sources have at most 12 hot items",
                severity="info",
            )
        )

    projection_status, projection_findings, _payload = _projection_status(
        root,
        settings.projection_path,
        sources,
    )
    findings.extend(projection_findings)
    overdue_sources = [
        source["path"]
        for source in sources
        if source.get("present") is True and source.get("state") == "overdue"
    ]
    closure_blocking = bool(overdue_sources) and projection_status != "fresh"
    if closure_blocking:
        readiness = "blocked"
    elif state in {"due", "unavailable"}:
        readiness = "advisory"
    else:
        readiness = "ready"
    return {
        "schema": EVALUATION_SCHEMA,
        "state": state,
        "readiness": readiness,
        "hot_count": sum(
            int(source["hot_count"])
            for source in sources
            if isinstance(source.get("hot_count"), int)
        ),
        "total_count": sum(
            int(source["total_count"])
            for source in sources
            if isinstance(source.get("total_count"), int)
        ),
        "source_count": len(sources),
        "sources": sources,
        "selected_count": len(selected_items),
        "selected_items": selected_items,
        "projection": {
            "path": settings.projection_path,
            "status": projection_status,
        },
        "overdue_sources": overdue_sources,
        "closure_blocking": closure_blocking,
        "findings": findings,
    }


def _now_text(value: str | datetime | None) -> str:
    if isinstance(value, datetime):
        moment = value
    elif value:
        text = str(value).strip()
        parsed_text = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            moment = datetime.fromisoformat(parsed_text)
        except ValueError as exc:
            raise StateProjectionError(f"invalid --now timestamp: {value}") from exc
    else:
        moment = datetime.now(timezone.utc).astimezone()
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.isoformat(timespec="seconds")


def _projection_payload(
    evaluation: dict[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    sources = []
    for source in evaluation["sources"]:
        sources.append(
            {
                "adapter": source["adapter"],
                "path": source["path"],
                "present": source["present"],
                "digest": source["digest"],
                "total_count": source["total_count"],
                "hot_count": source["hot_count"],
                "cold_count": source["cold_count"],
                "state": source["state"],
                "selected_count": source["selected_count"],
                "selected_items": source["selected_items"],
                "finding_codes": source["finding_codes"],
            }
        )
    return {
        "schema": PROJECTION_SCHEMA,
        "generated_at": generated_at,
        "projection_path": evaluation["projection"]["path"],
        "state": evaluation["state"],
        "hot_count": evaluation["hot_count"],
        "total_count": evaluation["total_count"],
        "source_count": evaluation["source_count"],
        "selected_count": evaluation["selected_count"],
        "sources": sources,
        "finding_codes": sorted(
            {
                str(finding.get("code"))
                for finding in evaluation["findings"]
                if str(finding.get("code") or "")
                not in {"projection-missing", "projection-stale", "projection-fresh"}
            }
        ),
    }


def write_projection(
    root: Path,
    *,
    now: str | datetime | None = None,
    config: _config.AgentRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Atomically write only the configured generated projection."""

    root = root.resolve()
    evaluation = evaluate_state(root, config=config)
    blocking_finding = next(
        (
            finding
            for finding in evaluation["findings"]
            if finding.get("code") in {"config-invalid", "projection-unsafe"}
        ),
        None,
    )
    if blocking_finding is not None:
        raise StateProjectionError(
            str(
                blocking_finding.get("detail")
                or "state projection configuration is invalid"
            )
        )
    relative = str(evaluation["projection"]["path"])
    target = _safe_target(root, relative)
    symlink = _symlink_ancestor(root, target)
    if symlink is not None:
        raise StateProjectionError(
            f"projection target or ancestor must not be a symlink: {relative}"
        )
    if not _is_inside(root, target.parent):
        raise StateProjectionError(f"projection parent resolves outside host root: {relative}")

    payload = _projection_payload(evaluation, generated_at=_now_text(now))
    encoded = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_PROJECTION_BYTES:
        raise StateProjectionError(
            f"projection exceeds the {MAX_PROJECTION_BYTES}-byte output limit"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
    return evaluate_state(root, config=config)


def compact_summary(evaluation: dict[str, Any]) -> str:
    hot = evaluation.get("hot_count", 0)
    source_count = evaluation.get("source_count", 0)
    projection = evaluation.get("projection", {})
    return (
        f"state={evaluation.get('state', 'unavailable')} "
        f"hot={hot} sources={source_count} "
        f"projection={projection.get('status', 'missing')} "
        f"readiness={evaluation.get('readiness', 'advisory')}"
    )
