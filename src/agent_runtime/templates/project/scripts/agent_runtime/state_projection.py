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
CLEANUP_PLAN_SCHEMA = "agent-runtime-scribe-cleanup-plan/v1"
CLEANUP_RECEIPT_SCHEMA = "agent-runtime-scribe-cleanup-receipt/v1"
OWNER_DECISION_SCHEMA = "agent-runtime-scribe-owner-decision/v1"
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
MAX_ACTIVE_RECORD_BYTES = 256 * 1024
MAX_ACTIVE_TASK_FILES = 512
MAX_ACTIVE_CLAIM_FILES = 512
MAX_ACTIVE_IDENTITIES = 64
MAX_CLEANUP_CANDIDATES = 10
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
_RECORD_ID_RE = re.compile(
    r"\b(?:TASK|UNIT|CLAIM|CYCLE|REVIEW|AUDIT|RETRO|MEETING|SEMINAR|"
    r"COUNCIL|BUG|BTC)-[A-Za-z0-9][A-Za-z0-9._-]*\b",
    re.IGNORECASE,
)
_PROTECTED_RECORD_PREFIXES = (
    "TASK-",
    "UNIT-",
    "CLAIM-",
    "CYCLE-",
    "REVIEW-",
    "AUDIT-",
    "RETRO-",
    "MEETING-",
    "SEMINAR-",
    "COUNCIL-",
    "BUG-",
    "BTC-",
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
_ACTIVE_WORK_STATUSES = {
    "active",
    "blocked",
    "claimed",
    "in_progress",
    "in-progress",
    "review",
    "verification",
    "waiting_review",
    "working",
}
_CLEANUP_AUTHORIZED_ROLES = {"lead-engineer", "doc-steward", "owner"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TASK_AUTHORIZATION_FIELDS = {
    "schema_version",
    "id",
    "work_id",
    "kind",
    "status",
    "scribe_authorization",
    "scribe_authorized_by",
    "scribe_authorized_role",
    "scribe_source_binding_digest",
    "scribe_cleanup_plan_digest",
}
_OWNER_DECISION_FIELDS = {
    "schema",
    "decision",
    "work_id",
    "authorization_ref",
    "source_binding_digest",
    "cleanup_plan_digest",
    "approved_by",
    "approver_role",
    "decided_at",
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
    cold_candidates: list[dict[str, Any]] = []
    total_count = 0
    hot_count = 0
    cold_count = 0
    nearest_heading = ""
    nearest_heading_ids: list[str] = []

    for index, line in enumerate(text.splitlines()):
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            raw_heading = _strip_heading_suffix(heading_match.group(2))
            heading = redact_text(
                raw_heading,
                limit=MAX_HEADING_CHARS,
            )
            if heading:
                nearest_heading = heading
                nearest_heading_ids = _record_ids(raw_heading)
                headings.append(
                    {
                        "heading": heading,
                        "level": len(heading_match.group(1)),
                        "source_order": index,
                        **(
                            {"_record_ids": nearest_heading_ids}
                            if nearest_heading_ids
                            else {}
                        ),
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
            raw_checkbox_item = checkbox_match.group(2)
            item = redact_text(raw_checkbox_item, limit=MAX_ITEM_CHARS)
            record_ids = sorted(
                {
                    *nearest_heading_ids,
                    *_record_ids(raw_checkbox_item),
                }
            )
            if checked:
                cold_count += 1
                cold_candidates.append(
                    {
                        "heading": nearest_heading,
                        "item": item or "[REDACTED]",
                        "checklist": "checked",
                        "source_order": index,
                        "_priority": 0,
                        **({"_record_ids": record_ids} if record_ids else {}),
                    }
                )
                continue
            hot_count += 1
            candidates.append(
                {
                    "heading": nearest_heading,
                    "item": item or "[REDACTED]",
                    "checklist": "unchecked",
                    "source_order": index,
                    "_priority": 0,
                    **({"_record_ids": record_ids} if record_ids else {}),
                }
            )
            continue

        hot_count += 1
        item = redact_text(raw_item, limit=MAX_ITEM_CHARS)
        record_ids = sorted(
            {
                *nearest_heading_ids,
                *_record_ids(raw_item),
            }
        )
        candidates.append(
            {
                "heading": nearest_heading,
                "item": item or "[REDACTED]",
                "checklist": "none",
                "source_order": index,
                "_priority": 1,
                **({"_record_ids": record_ids} if record_ids else {}),
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
                **(
                    {"_record_ids": heading["_record_ids"]}
                    if heading.get("_record_ids")
                    else {}
                ),
            }
            for heading in headings
        ]

    # The bounded hot view keeps the newest records within each priority class.
    # Older unselected records can then be proposed as cold history without
    # pretending that a projection itself archived anything.
    candidates.sort(key=lambda item: (item["_priority"], -item["source_order"]))
    cold_candidates.sort(key=lambda item: item["source_order"])
    return {
        "total_count": total_count,
        "hot_count": hot_count,
        "cold_count": cold_count,
        "candidates": candidates,
        "cold_candidates": cold_candidates,
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
    cold_candidates: list[dict[str, Any]] = []
    hot_count = 0
    cold_count = 0
    for index, entry in enumerate(entries):
        item, status = _json_item(entry)
        if isinstance(entry, dict):
            raw_identity_fields = " ".join(
                str(entry.get(key) or "") for key in _JSON_VALUE_KEYS
            )
        else:
            raw_identity_fields = str(entry or "")
        record_ids = _record_ids(raw_identity_fields)
        cold = status.strip().lower() in _COLD_JSON_STATUSES
        if cold:
            cold_count += 1
            if item:
                cold_candidates.append(
                    {
                        "heading": "",
                        "item": item,
                        "checklist": "closed-status",
                        "source_order": index,
                        "_priority": 0,
                        **({"_record_ids": record_ids} if record_ids else {}),
                    }
                )
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
                **({"_record_ids": record_ids} if record_ids else {}),
            }
        )
    candidates.sort(key=lambda item: (item["_priority"], -item["source_order"]))
    return {
        "total_count": len(entries),
        "hot_count": hot_count,
        "cold_count": cold_count,
        "candidates": candidates,
        "cold_candidates": cold_candidates,
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


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _frontmatter_scalar(text: str, field: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(rf"^\s*{re.escape(field)}\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value.strip()
    return ""


def _active_status(value: object) -> bool:
    normalized = re.sub(r"\s+", "_", str(value or "").strip().lower())
    return normalized in _ACTIVE_WORK_STATUSES or normalized in {
        "진행_중",
        "검토_중",
        "차단",
    }


def _overlay_marker(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _read_bounded_text(path: Path, limit: int) -> str:
    if path.stat().st_size > limit:
        raise StateProjectionError(f"record exceeds the {limit}-byte read limit")
    return path.read_text(encoding="utf-8")


def _safe_discovered_record(root: Path, path: Path) -> Path:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise StateProjectionError("discovered record is outside host root") from exc
    target = _safe_target(root, relative)
    symlink = _symlink_ancestor(root, target)
    if symlink is not None:
        raise StateProjectionError(
            f"discovered record or ancestor must not be a symlink: {relative}"
        )
    return target


def _discover_active_work(
    root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Return bounded canonical active task and non-overlay claim identities."""

    findings: list[dict[str, str]] = []
    task_ids: set[str] = set()
    claim_ids: set[str] = set()
    task_paths = sorted(
        (root / "agents" / "lead_engineer" / "tasks").glob("TASK-*.md")
    )[:MAX_ACTIVE_TASK_FILES]
    for path in task_paths:
        try:
            target = _safe_discovered_record(root, path)
            text = _read_bounded_text(target, MAX_ACTIVE_RECORD_BYTES)
        except (OSError, UnicodeError, StateProjectionError) as exc:
            findings.append(
                _finding(
                    "active-task-unreadable",
                    path=path.relative_to(root).as_posix(),
                    detail=str(exc),
                )
            )
            continue
        if not _active_status(_frontmatter_scalar(text, "status")):
            continue
        task_id = (
            _frontmatter_scalar(text, "id")
            or _frontmatter_scalar(text, "work_id")
            or path.stem
        )
        if task_id:
            task_ids.add(_bounded(task_id, 160))

    claim_paths = sorted(
        (root / "agents" / "runtime" / "task_claims").glob("*.json")
    )[:MAX_ACTIVE_CLAIM_FILES]
    for path in claim_paths:
        try:
            target = _safe_discovered_record(root, path)
            payload = json.loads(
                _read_bounded_text(target, MAX_ACTIVE_RECORD_BYTES)
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            StateProjectionError,
        ) as exc:
            findings.append(
                _finding(
                    "active-claim-unreadable",
                    path=path.relative_to(root).as_posix(),
                    detail=str(exc),
                )
            )
            continue
        if (
            not isinstance(payload, dict)
            or not _active_status(payload.get("status"))
            or _overlay_marker(payload.get("overlay"))
        ):
            continue
        claim_id = _bounded(payload.get("claim_id") or path.stem, 180)
        task_id = _bounded(payload.get("task_id"), 160)
        if claim_id:
            claim_ids.add(claim_id)
        if task_id:
            task_ids.add(task_id)

    all_tasks = sorted(task_ids)
    all_claims = sorted(claim_ids)
    overflow = (
        len(all_tasks) > MAX_ACTIVE_IDENTITIES
        or len(all_claims) > MAX_ACTIVE_IDENTITIES
        or len(task_paths) >= MAX_ACTIVE_TASK_FILES
        or len(claim_paths) >= MAX_ACTIVE_CLAIM_FILES
    )
    visible_tasks = all_tasks[:MAX_ACTIVE_IDENTITIES]
    visible_claims = all_claims[:MAX_ACTIVE_IDENTITIES]
    digest_payload = {
        "task_ids": visible_tasks,
        "claim_ids": visible_claims,
        "task_count": len(all_tasks),
        "claim_count": len(all_claims),
        "overflow": overflow,
    }
    if overflow:
        findings.append(
            _finding(
                "active-work-overflow",
                path="agents/runtime/task_claims",
                detail=(
                    "active identity discovery exceeded its bounded view; "
                    "coverage cannot be declared complete"
                ),
            )
        )
    return {
        "schema": "agent-runtime-scribe-active-work/v1",
        **digest_payload,
        "digest": _canonical_digest(digest_payload),
    }, findings


def _record_ids(value: object) -> list[str]:
    return sorted(
        {
            match.group(0).upper()
            for match in _RECORD_ID_RE.finditer(str(value or ""))
        }
    )


def _cleanup_plan(
    *,
    sources: list[dict[str, Any]],
    hot_candidates: list[list[dict[str, Any]]],
    cold_candidates: list[list[dict[str, Any]]],
    selected_orders: list[set[int]],
    active_work: dict[str, Any],
) -> dict[str, Any]:
    active_ids = {
        *[str(value).upper() for value in active_work.get("task_ids", [])],
        *[str(value).upper() for value in active_work.get("claim_ids", [])],
    }
    proposed: list[dict[str, Any]] = []
    excluded: dict[str, int] = {}

    if not active_work.get("overflow"):
        for source, hot, cold, kept in zip(
            sources,
            hot_candidates,
            cold_candidates,
            selected_orders,
        ):
            source_candidates: list[tuple[dict[str, Any], str]] = [
                (candidate, "completed-record") for candidate in cold
            ]
            source_candidates.extend(
                (candidate, "outside-hot-window")
                for candidate in hot
                if int(candidate.get("source_order", -1)) not in kept
            )
            source_candidates.sort(
                key=lambda pair: int(pair[0].get("source_order", 0))
            )
            for candidate, reason in source_candidates:
                item = str(candidate.get("item") or "")
                heading = str(candidate.get("heading") or "")
                ids = {
                    *[
                        str(record_id).upper()
                        for record_id in candidate.get("_record_ids", [])
                    ],
                    *_record_ids(f"{heading} {item}"),
                }
                exclusion = ""
                if item == "[REDACTED]":
                    exclusion = "redacted"
                elif active_ids.intersection(ids):
                    exclusion = "active-reference"
                elif any(
                    record_id.startswith(_PROTECTED_RECORD_PREFIXES)
                    for record_id in ids
                ):
                    exclusion = "canonical-reference"
                if exclusion:
                    excluded[exclusion] = excluded.get(exclusion, 0) + 1
                    continue
                if len(proposed) >= MAX_CLEANUP_CANDIDATES:
                    excluded["candidate-budget"] = (
                        excluded.get("candidate-budget", 0) + 1
                    )
                    continue
                proposed.append(
                    {
                        "adapter": source["adapter"],
                        "path": source["path"],
                        "heading": heading,
                        "item": item,
                        "checklist": candidate.get("checklist", "none"),
                        "source_order": int(candidate.get("source_order", 0)),
                        "reason": reason,
                        "cold_history": True,
                    }
                )

    core = {
        "schema": CLEANUP_PLAN_SCHEMA,
        "active_work_digest": active_work.get("digest"),
        "source_fingerprints": [
            {
                "adapter": source.get("adapter"),
                "path": source.get("path"),
                "present": source.get("present"),
                "digest": source.get("digest"),
            }
            for source in sources
        ],
        "candidates": proposed,
        "excluded_reason_counts": dict(sorted(excluded.items())),
    }
    if active_work.get("overflow"):
        status = "blocked_active_overflow"
    elif proposed:
        status = "available"
    else:
        status = "empty"
    return {
        **core,
        "status": status,
        "candidate_count": len(proposed),
        "excluded_count": sum(excluded.values()),
        "plan_digest": _canonical_digest(core),
    }


def _evaluate_source(
    root: Path,
    source: StateSource,
) -> tuple[
    dict[str, Any],
    list[dict[str, str]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
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
        return base, findings, [], []
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
        return base, findings, [], []
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
            return base, findings, [], []
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
        return base, findings, [], []

    base.update(
        present=True,
        digest=_source_digest(raw),
        total_count=parsed["total_count"],
        hot_count=parsed["hot_count"],
        cold_count=parsed["cold_count"],
        state=classify_hot_count(parsed["hot_count"]),
    )
    return (
        base,
        findings,
        list(parsed["candidates"]),
        list(parsed["cold_candidates"]),
    )


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
    except (OSError, UnicodeError, json.JSONDecodeError, StateProjectionError) as exc:
        findings.append(
            _finding(
                "projection-stale",
                path=projection_path,
                detail=str(exc),
            )
        )
        return "stale", findings, None

    if _fingerprints(projected_sources) != _fingerprints(sources):
        findings.append(
            _finding(
                "projection-stale",
                path=projection_path,
                detail="projection source paths or digests are stale",
            )
        )
        # A structurally valid stale payload is still required as the bounded
        # "before" side of an explicitly authorized cleanup receipt.
        return "stale", findings, payload

    findings.append(
        _finding(
            "projection-fresh",
            path=projection_path,
            detail="all present source paths and SHA-256 digests match",
            severity="info",
        )
    )
    return "fresh", findings, payload


def _active_coverage(
    current: dict[str, Any],
    projected_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    projected = (
        projected_payload.get("active_work")
        if isinstance(projected_payload, dict)
        else None
    )
    if not isinstance(projected, dict):
        projected = {}
    current_tasks = {str(value) for value in current.get("task_ids", [])}
    current_claims = {str(value) for value in current.get("claim_ids", [])}
    projected_tasks = {str(value) for value in projected.get("task_ids", [])}
    projected_claims = {str(value) for value in projected.get("claim_ids", [])}
    missing_tasks = sorted(current_tasks - projected_tasks)
    missing_claims = sorted(current_claims - projected_claims)
    stale_tasks = sorted(projected_tasks - current_tasks)
    stale_claims = sorted(projected_claims - current_claims)
    complete = not (
        current.get("overflow")
        or projected.get("overflow")
        or missing_tasks
        or missing_claims
        or stale_tasks
        or stale_claims
    )
    return {
        "status": "complete" if complete else "incomplete",
        "current_task_ids": sorted(current_tasks),
        "current_claim_ids": sorted(current_claims),
        "projected_task_ids": sorted(projected_tasks),
        "projected_claim_ids": sorted(projected_claims),
        "missing_task_ids": missing_tasks,
        "missing_claim_ids": missing_claims,
        "stale_task_ids": stale_tasks,
        "stale_claim_ids": stale_claims,
        "overflow": bool(current.get("overflow") or projected.get("overflow")),
        "active_work_digest": current.get("digest"),
    }


def _receipt_sources(sources: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "adapter": source.get("adapter"),
            "path": source.get("path"),
            "present": source.get("present"),
            "digest": source.get("digest"),
            "hot_count": source.get("hot_count"),
        }
        for source in sources
    ]


def _validated_receipt_sources(
    value: object,
    *,
    label: str,
) -> tuple[list[dict[str, Any]], int]:
    if not isinstance(value, list) or not value or len(value) > MAX_SOURCES:
        raise StateProjectionError(
            f"{label} must contain 1 to {MAX_SOURCES} source bindings"
        )
    rows: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    hot_count = 0
    for index, source in enumerate(value):
        if not isinstance(source, dict):
            raise StateProjectionError(f"{label}[{index}] must be an object")
        adapter = source.get("adapter")
        path = source.get("path")
        present = source.get("present")
        digest = source.get("digest")
        source_hot = source.get("hot_count")
        if (
            not isinstance(adapter, str)
            or not adapter.strip()
            or len(adapter) > 80
        ):
            raise StateProjectionError(f"{label}[{index}] adapter is invalid")
        if (
            not isinstance(path, str)
            or not path
            or len(path) > 512
            or "\\" in path
            or Path(path).is_absolute()
            or any(part in {"", ".", ".."} for part in Path(path).parts)
        ):
            raise StateProjectionError(f"{label}[{index}] path is invalid")
        if not isinstance(present, bool):
            raise StateProjectionError(f"{label}[{index}] presence is invalid")
        identity = (adapter, path)
        if identity in identities:
            raise StateProjectionError(f"{label}[{index}] identity is duplicated")
        identities.add(identity)
        if present:
            if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                raise StateProjectionError(f"{label}[{index}] digest is invalid")
            if (
                isinstance(source_hot, bool)
                or not isinstance(source_hot, int)
                or source_hot < 0
            ):
                raise StateProjectionError(f"{label}[{index}] hot count is invalid")
            hot_count += source_hot
        elif digest is not None or source_hot is not None:
            raise StateProjectionError(
                f"{label}[{index}] absent source carries digest or hot count"
            )
        rows.append(
            {
                "adapter": adapter,
                "path": path,
                "present": present,
                "digest": digest,
                "hot_count": source_hot,
            }
        )
    return rows, hot_count


def _source_binding_digest(sources: list[dict[str, Any]]) -> str:
    return _canonical_digest(sources)


def _validated_cleanup_plan(
    value: object,
    *,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StateProjectionError("baseline cleanup plan must be an object")
    core_fields = {
        "schema",
        "active_work_digest",
        "source_fingerprints",
        "candidates",
        "excluded_reason_counts",
    }
    expected_fields = {
        *core_fields,
        "status",
        "candidate_count",
        "excluded_count",
        "plan_digest",
    }
    if set(value) != expected_fields:
        raise StateProjectionError("baseline cleanup plan fields are invalid")
    if value.get("schema") != CLEANUP_PLAN_SCHEMA:
        raise StateProjectionError("baseline cleanup plan schema is invalid")
    active_digest = value.get("active_work_digest")
    if not isinstance(active_digest, str) or _SHA256_RE.fullmatch(active_digest) is None:
        raise StateProjectionError(
            "baseline cleanup plan active-work digest is invalid"
        )
    expected_fingerprints = [
        {
            "adapter": source["adapter"],
            "path": source["path"],
            "present": source["present"],
            "digest": source["digest"],
        }
        for source in sources
    ]
    if value.get("source_fingerprints") != expected_fingerprints:
        raise StateProjectionError(
            "baseline cleanup plan source fingerprints do not match its sources"
        )
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or len(candidates) > MAX_CLEANUP_CANDIDATES:
        raise StateProjectionError("baseline cleanup plan candidates are invalid")
    candidate_fields = {
        "adapter",
        "path",
        "heading",
        "item",
        "checklist",
        "source_order",
        "reason",
        "cold_history",
    }
    source_identities = {
        (source["adapter"], source["path"]) for source in sources
    }
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or set(candidate) != candidate_fields:
            raise StateProjectionError(
                f"baseline cleanup plan candidate {index} is invalid"
            )
        if (
            (candidate.get("adapter"), candidate.get("path"))
            not in source_identities
            or not isinstance(candidate.get("heading"), str)
            or len(candidate["heading"]) > MAX_HEADING_CHARS
            or not isinstance(candidate.get("item"), str)
            or len(candidate["item"]) > MAX_ITEM_CHARS
            or candidate.get("checklist") not in {
                "none",
                "unchecked",
                "checked",
                "heading",
            }
            or isinstance(candidate.get("source_order"), bool)
            or not isinstance(candidate.get("source_order"), int)
            or candidate["source_order"] < 0
            or candidate.get("reason") not in {
                "completed-record",
                "outside-hot-window",
            }
            or candidate.get("cold_history") is not True
        ):
            raise StateProjectionError(
                f"baseline cleanup plan candidate {index} is invalid"
            )
    excluded = value.get("excluded_reason_counts")
    if (
        not isinstance(excluded, dict)
        or any(
            not isinstance(key, str)
            or not key
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            for key, count in excluded.items()
        )
    ):
        raise StateProjectionError(
            "baseline cleanup plan exclusion counts are invalid"
        )
    if value.get("candidate_count") != len(candidates):
        raise StateProjectionError(
            "baseline cleanup plan candidate count is inconsistent"
        )
    if value.get("excluded_count") != sum(excluded.values()):
        raise StateProjectionError(
            "baseline cleanup plan excluded count is inconsistent"
        )
    status = value.get("status")
    if status not in {"available", "empty", "blocked_active_overflow"}:
        raise StateProjectionError("baseline cleanup plan status is invalid")
    if (status == "available") != bool(candidates):
        raise StateProjectionError(
            "baseline cleanup plan status and candidates are inconsistent"
        )
    core = {field: value[field] for field in core_fields}
    if value.get("plan_digest") != _canonical_digest(core):
        raise StateProjectionError("baseline cleanup plan digest is invalid")
    return json.loads(json.dumps(value, ensure_ascii=False))


def _validated_projection_baseline(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, dict[str, Any], str]:
    try:
        sources, hot_count = _validated_receipt_sources(
            payload.get("sources"),
            label="baseline sources",
        )
        if payload.get("hot_count") != hot_count:
            raise StateProjectionError(
                "baseline top-level hot count does not match source counts"
            )
        if payload.get("source_count") != len(sources):
            raise StateProjectionError(
                "baseline source count does not match source bindings"
            )
        source_debt = payload.get("source_debt")
        if (
            not isinstance(source_debt, dict)
            or source_debt.get("hot_count") != hot_count
        ):
            raise StateProjectionError(
                "baseline source-debt hot count is inconsistent"
            )
        plan = _validated_cleanup_plan(
            payload.get("cleanup_plan"),
            sources=sources,
        )
        active_work = payload.get("active_work")
        if (
            not isinstance(active_work, dict)
            or active_work.get("digest") != plan.get("active_work_digest")
        ):
            raise StateProjectionError(
                "baseline active-work and cleanup-plan bindings disagree"
            )
    except StateProjectionError as exc:
        if str(exc).startswith("baseline"):
            raise
        raise StateProjectionError(f"baseline is invalid: {exc}") from exc
    return sources, hot_count, plan, _source_binding_digest(sources)


def _safe_existing_ref(
    root: Path,
    relative: object,
    *,
    record_kind: str,
) -> str:
    value = str(relative or "").strip()
    if not value or Path(value).is_absolute():
        return ""
    try:
        target = _safe_target(root, value)
    except StateProjectionError:
        return ""
    if _symlink_ancestor(root, target) is not None or not target.is_file():
        return ""
    relative_path = Path(value)
    parts = relative_path.parts
    is_task = (
        len(parts) == 4
        and parts[:3] == ("agents", "lead_engineer", "tasks")
        and relative_path.suffix.lower() == ".md"
        and relative_path.name.startswith("TASK-")
    )
    is_unit = (
        len(parts) == 6
        and parts[:4] == ("agents", "lead_engineer", "tasks", "units")
        and parts[4].startswith("TASK-")
        and relative_path.suffix.lower() == ".md"
        and relative_path.name.startswith("UNIT-TASK-")
    )
    is_owner_record = (
        len(parts) == 2
        and parts[0] == "reviews"
        and relative_path.suffix.lower() == ".json"
        and relative_path.name.startswith(("DECISION-", "OWNER-DECISION-"))
    )
    if record_kind == "task_authorization" and not (is_task or is_unit):
        return ""
    if record_kind == "owner_decision" and not is_owner_record:
        return ""
    return relative_path.as_posix()


def _authority_identity(value: object) -> bool:
    text = str(value or "").strip()
    return (
        bool(text)
        and len(text) <= 160
        and redact_text(text, limit=160) == text
        and not any(character in text for character in "\r\n")
    )


def _authorization_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise StateProjectionError("TASK authorization frontmatter is missing")
    values: dict[str, str] = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$", line)
        if not match or match.group(1) not in _TASK_AUTHORIZATION_FIELDS:
            continue
        field = match.group(1)
        if field in values:
            raise StateProjectionError(
                f"TASK authorization repeats field {field}"
            )
        value = match.group(2).strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]
        values[field] = value.strip()
    if not closed:
        raise StateProjectionError("TASK authorization frontmatter is unterminated")
    return values


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise StateProjectionError(f"owner decision repeats field {key}")
        payload[key] = value
    return payload


def _validate_task_authorization(
    root: Path,
    relative: object,
    *,
    source_binding_digest: str,
    cleanup_plan_digest: str,
) -> tuple[str, str]:
    ref = _safe_existing_ref(
        root,
        relative,
        record_kind="task_authorization",
    )
    if not ref:
        raise StateProjectionError(
            "cleanup receipt requires an existing bound TASK authorization"
        )
    try:
        text = _read_bounded_text(
            _safe_target(root, ref),
            MAX_ACTIVE_RECORD_BYTES,
        )
    except (OSError, UnicodeError, StateProjectionError) as exc:
        raise StateProjectionError(
            "cleanup receipt requires an existing bound TASK authorization"
        ) from exc
    path = Path(ref)
    try:
        fields = _authorization_frontmatter(text)
    except StateProjectionError as exc:
        raise StateProjectionError(
            "cleanup receipt requires an existing bound TASK authorization"
        ) from exc
    work_id = fields.get("work_id") or fields.get("id") or ""
    kind = fields.get("kind", "")
    expected_kind = "unit" if path.name.startswith("UNIT-TASK-") else "task"
    if (
        fields.get("schema_version") != "agent-runtime-work-item/v1"
        or work_id != path.stem
        or kind != expected_kind
        or not _active_status(fields.get("status"))
        or fields.get("scribe_authorization") != "cleanup"
        or fields.get("scribe_source_binding_digest")
        != source_binding_digest
        or fields.get("scribe_cleanup_plan_digest") != cleanup_plan_digest
        or fields.get("scribe_authorized_role")
        not in _CLEANUP_AUTHORIZED_ROLES
        or not _authority_identity(fields.get("scribe_authorized_by"))
    ):
        raise StateProjectionError(
            "cleanup receipt requires an existing bound TASK authorization"
        )
    return ref, work_id


def _valid_decided_at(value: object) -> bool:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text
        )
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_owner_decision(
    root: Path,
    relative: object,
    *,
    authorization_ref: str,
    authorization_work_id: str,
    source_binding_digest: str,
    cleanup_plan_digest: str,
) -> str:
    ref = _safe_existing_ref(root, relative, record_kind="owner_decision")
    if not ref:
        raise StateProjectionError(
            "cleanup receipt requires a bound owner no-touch decision"
        )
    try:
        payload = json.loads(
            _read_bounded_text(
                _safe_target(root, ref),
                MAX_ACTIVE_RECORD_BYTES,
            ),
            object_pairs_hook=_unique_json_object,
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        StateProjectionError,
    ) as exc:
        raise StateProjectionError(
            "cleanup receipt requires a bound owner no-touch decision"
        ) from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != _OWNER_DECISION_FIELDS
        or payload.get("schema") != OWNER_DECISION_SCHEMA
        or payload.get("decision") != "no_touch"
        or payload.get("work_id") != authorization_work_id
        or payload.get("authorization_ref") != authorization_ref
        or payload.get("source_binding_digest") != source_binding_digest
        or payload.get("cleanup_plan_digest") != cleanup_plan_digest
        or payload.get("approver_role") != "owner"
        or not _authority_identity(payload.get("approved_by"))
        or not _valid_decided_at(payload.get("decided_at"))
    ):
        raise StateProjectionError(
            "cleanup receipt requires a bound owner no-touch decision"
        )
    return ref


def _cleanup_outcome(
    root: Path,
    *,
    projection_status: str,
    projected_payload: dict[str, Any] | None,
    sources: list[dict[str, Any]],
    active_work: dict[str, Any],
    hot_count: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    receipt = (
        projected_payload.get("cleanup_receipt")
        if isinstance(projected_payload, dict)
        else None
    )
    if receipt is None:
        return {"status": "none", "valid": False}, []
    if not isinstance(receipt, dict):
        return (
            {"status": "invalid", "valid": False},
            [
                _finding(
                    "cleanup-outcome-invalid",
                    path=".",
                    detail="cleanup receipt must be an object",
                )
            ],
        )
    errors: list[str] = []
    if projection_status != "fresh":
        errors.append("projection is not fresh")
    if receipt.get("schema") != CLEANUP_RECEIPT_SCHEMA:
        errors.append("receipt schema is invalid")
    receipt_core = {
        key: value
        for key, value in receipt.items()
        if key != "receipt_digest"
    }
    if receipt.get("receipt_digest") != _canonical_digest(receipt_core):
        errors.append("receipt digest does not match its payload")
    if receipt.get("after_sources") != _receipt_sources(sources):
        errors.append("receipt after-source bindings do not match current sources")
    if receipt.get("resulting_hot_count") != hot_count:
        errors.append("receipt resulting hot count does not match current sources")
    before_sources: list[dict[str, Any]] = []
    before_hot = -1
    source_binding_digest = ""
    try:
        before_sources, before_hot = _validated_receipt_sources(
            receipt.get("before_sources"),
            label="receipt before sources",
        )
        source_binding_digest = _source_binding_digest(before_sources)
    except StateProjectionError as exc:
        errors.append(str(exc))
    if receipt.get("before_hot_count") != before_hot:
        errors.append("receipt before hot count does not match before sources")
    if receipt.get("before_source_binding_digest") != source_binding_digest:
        errors.append("receipt before-source binding digest is invalid")

    before_plan: dict[str, Any] = {}
    try:
        before_plan = _validated_cleanup_plan(
            receipt.get("before_cleanup_plan"),
            sources=before_sources,
        )
    except StateProjectionError as exc:
        errors.append(str(exc))
    cleanup_plan_digest = str(receipt.get("cleanup_plan_digest") or "")
    if (
        not before_plan
        or cleanup_plan_digest != before_plan.get("plan_digest")
    ):
        errors.append("receipt cleanup-plan digest is invalid")
    active_digest = active_work.get("digest")
    if (
        receipt.get("active_work_digest") != active_digest
        or before_plan.get("active_work_digest") != active_digest
    ):
        errors.append("receipt active-work binding is stale")

    before_identity = [
        (source["adapter"], source["path"], source["present"])
        for source in before_sources
    ]
    after_identity = [
        (
            source.get("adapter"),
            source.get("path"),
            source.get("present"),
        )
        for source in sources
    ]
    if before_identity != after_identity:
        errors.append("receipt source identities changed across cleanup")

    authorization = ""
    authorization_work_id = ""
    try:
        authorization, authorization_work_id = _validate_task_authorization(
            root,
            receipt.get("authorization_ref"),
            source_binding_digest=source_binding_digest,
            cleanup_plan_digest=cleanup_plan_digest,
        )
    except StateProjectionError as exc:
        errors.append(str(exc))
    if receipt.get("authorization_ref") != authorization:
        errors.append("receipt authorization ref is invalid")
    if receipt.get("authorization_work_id") != authorization_work_id:
        errors.append("receipt authorization work identity is invalid")

    outcome = str(receipt.get("outcome") or "")
    if outcome == "reduction":
        if before_hot <= hot_count:
            errors.append("reduction receipt did not reduce hot count")
        if receipt.get("owner_decision_ref") not in {None, ""}:
            errors.append("reduction receipt must not cite an owner decision")
        status = "verified_reduction"
    elif outcome == "owner_decision":
        try:
            owner_decision = _validate_owner_decision(
                root,
                receipt.get("owner_decision_ref"),
                authorization_ref=authorization,
                authorization_work_id=authorization_work_id,
                source_binding_digest=source_binding_digest,
                cleanup_plan_digest=cleanup_plan_digest,
            )
        except StateProjectionError as exc:
            errors.append(str(exc))
            owner_decision = ""
        if receipt.get("owner_decision_ref") != owner_decision:
            errors.append("receipt owner decision ref is invalid")
        status = "owner_decision"
    else:
        errors.append("receipt outcome is unsupported")
        status = "invalid"

    if errors:
        return (
            {
                "status": "invalid",
                "valid": False,
                "errors": errors,
            },
            [
                _finding(
                    "cleanup-outcome-invalid",
                    path=".",
                    detail="; ".join(errors),
                )
            ],
        )
    return (
        {
            "status": status,
            "valid": True,
            "authorization_ref": receipt.get("authorization_ref"),
            "owner_decision_ref": receipt.get("owner_decision_ref"),
            "receipt_digest": receipt.get("receipt_digest"),
        },
        [
            _finding(
                "cleanup-outcome-verified",
                path=".",
                detail=f"cleanup outcome is {status}",
                severity="info",
            )
        ],
    )


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
    source_cold_candidates: list[list[dict[str, Any]]] = []
    for source in settings.sources:
        evaluated, source_findings, candidates, cold_candidates = _evaluate_source(
            root, source
        )
        sources.append(evaluated)
        source_candidates.append(candidates)
        source_cold_candidates.append(cold_candidates)
        findings.extend(source_findings)

    active_work, active_findings = _discover_active_work(root)
    findings.extend(active_findings)
    remaining = MAX_SELECTED_ITEMS
    selected_items: list[dict[str, Any]] = []
    selected_orders: list[set[int]] = []
    for source, candidates in zip(sources, source_candidates):
        selected: list[dict[str, Any]] = []
        kept_orders: set[int] = set()
        for candidate in candidates[:remaining]:
            clean = {
                "heading": candidate["heading"],
                "item": candidate["item"],
                "checklist": candidate["checklist"],
            }
            kept_orders.add(int(candidate.get("source_order", 0)))
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
        selected_orders.append(kept_orders)
        remaining -= len(selected)
        if remaining <= 0:
            remaining = 0

    cleanup_plan = _cleanup_plan(
        sources=sources,
        hot_candidates=source_candidates,
        cold_candidates=source_cold_candidates,
        selected_orders=selected_orders,
        active_work=active_work,
    )
    state = _overall_state(sources)
    hot_count = sum(
        int(source["hot_count"])
        for source in sources
        if isinstance(source.get("hot_count"), int)
    )
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

    projection_status, projection_findings, projected_payload = _projection_status(
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
    source_debt = {
        "status": state,
        "hot_count": hot_count,
        "overdue_sources": overdue_sources,
    }
    if overdue_sources:
        findings.append(
            _finding(
                "source-debt-overdue",
                path=".",
                detail=(
                    "overdue canonical source debt remains; a fresh projection "
                    "does not clear it"
                ),
            )
        )

    active_coverage = _active_coverage(active_work, projected_payload)
    if active_coverage["status"] == "complete":
        findings.append(
            _finding(
                "active-coverage-complete",
                path="agents/runtime/task_claims",
                detail="current task and non-overlay claim identities are represented",
                severity="info",
            )
        )
    else:
        findings.append(
            _finding(
                "active-coverage-incomplete",
                path="agents/runtime/task_claims",
                detail=(
                    "projection is missing or retaining active task/claim "
                    "identities; refresh the bounded projection"
                ),
            )
        )

    if cleanup_plan["status"] == "available":
        findings.append(
            _finding(
                "cleanup-plan-available",
                path=".",
                detail=(
                    f"{cleanup_plan['candidate_count']} bounded cold-history "
                    "candidate(s) require an explicit Scribe task"
                ),
                severity="info",
            )
        )
    elif cleanup_plan["status"] == "blocked_active_overflow":
        findings.append(
            _finding(
                "cleanup-plan-blocked",
                path=".",
                detail="active-work overflow prevents a safe cleanup proposal",
            )
        )

    cleanup_outcome, cleanup_findings = _cleanup_outcome(
        root,
        projection_status=projection_status,
        projected_payload=projected_payload,
        sources=sources,
        active_work=active_work,
        hot_count=hot_count,
    )
    findings.extend(cleanup_findings)
    owner_decision = (
        cleanup_outcome.get("valid") is True
        and cleanup_outcome.get("status") == "owner_decision"
    )
    closure_reasons: list[str] = []
    if overdue_sources and not owner_decision:
        closure_reasons.append("source-debt-overdue")
    if overdue_sources and projection_status != "fresh":
        closure_reasons.append("projection-not-fresh")
    if active_coverage["status"] != "complete":
        closure_reasons.append("active-coverage-incomplete")
    if cleanup_outcome.get("status") == "invalid":
        closure_reasons.append("cleanup-outcome-invalid")
    closure_blocking = bool(closure_reasons)
    if closure_blocking:
        readiness = "blocked"
    elif owner_decision and overdue_sources:
        readiness = "ready_with_owner_decision"
    elif state in {"due", "unavailable"}:
        readiness = "advisory"
    else:
        readiness = "ready"
    return {
        "schema": EVALUATION_SCHEMA,
        "state": state,
        "readiness": readiness,
        "hot_count": hot_count,
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
        "source_debt": source_debt,
        "active_work": active_work,
        "active_coverage": active_coverage,
        "cleanup_plan": cleanup_plan,
        "cleanup_outcome": cleanup_outcome,
        "overdue_sources": overdue_sources,
        "closure_blocking": closure_blocking,
        "closure_reasons": closure_reasons,
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
        "source_debt": evaluation["source_debt"],
        "hot_count": evaluation["hot_count"],
        "total_count": evaluation["total_count"],
        "source_count": evaluation["source_count"],
        "selected_count": evaluation["selected_count"],
        "sources": sources,
        "active_work": evaluation["active_work"],
        "cleanup_plan": evaluation["cleanup_plan"],
        "finding_codes": sorted(
            {
                str(finding.get("code"))
                for finding in evaluation["findings"]
                if str(finding.get("code") or "")
                not in {"projection-missing", "projection-stale", "projection-fresh"}
            }
        ),
    }


def _write_projection_payload(
    root: Path,
    *,
    relative: str,
    payload: dict[str, Any],
) -> None:
    target = _safe_target(root, relative)
    symlink = _symlink_ancestor(root, target)
    if symlink is not None:
        raise StateProjectionError(
            f"projection target or ancestor must not be a symlink: {relative}"
        )
    if not _is_inside(root, target.parent):
        raise StateProjectionError(
            f"projection parent resolves outside host root: {relative}"
        )
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
    payload = _projection_payload(evaluation, generated_at=_now_text(now))
    _write_projection_payload(root, relative=relative, payload=payload)
    return evaluate_state(root, config=config)


def record_cleanup(
    root: Path,
    *,
    authorization_ref: str,
    owner_decision_ref: str = "",
    now: str | datetime | None = None,
    config: _config.AgentRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Record an authorized cleanup outcome without editing canonical state."""

    root = root.resolve()
    evaluation = evaluate_state(root, config=config)
    relative = str(evaluation["projection"]["path"])
    _status, _findings, before_payload = _projection_status(
        root,
        relative,
        list(evaluation["sources"]),
    )
    if not isinstance(before_payload, dict):
        raise StateProjectionError(
            "cleanup receipt requires an existing structurally valid projection"
        )
    (
        before_sources,
        before_hot,
        prior_plan,
        source_binding_digest,
    ) = _validated_projection_baseline(before_payload)
    before_identity = [
        (
            source["adapter"],
            source["path"],
            source["present"],
        )
        for source in before_sources
    ]
    after_identity = [
        (
            str(source.get("adapter") or ""),
            str(source.get("path") or ""),
            source.get("present") is True,
        )
        for source in evaluation["sources"]
    ]
    if before_identity != after_identity:
        raise StateProjectionError(
            "cleanup receipt source adapters or paths changed since the baseline"
        )

    prior_plan_digest = str(prior_plan["plan_digest"])
    if (
        evaluation["active_coverage"]["status"] != "complete"
        or prior_plan.get("active_work_digest")
        != evaluation["active_work"].get("digest")
    ):
        raise StateProjectionError(
            "cleanup receipt baseline active-work coverage is incomplete or stale"
        )
    authorization, authorization_work_id = _validate_task_authorization(
        root,
        authorization_ref,
        source_binding_digest=source_binding_digest,
        cleanup_plan_digest=prior_plan_digest,
    )
    owner_decision = ""
    if owner_decision_ref:
        owner_decision = _validate_owner_decision(
            root,
            owner_decision_ref,
            authorization_ref=authorization,
            authorization_work_id=authorization_work_id,
            source_binding_digest=source_binding_digest,
            cleanup_plan_digest=prior_plan_digest,
        )

    after_hot = evaluation.get("hot_count")
    if not isinstance(after_hot, int):
        raise StateProjectionError("cleanup receipt requires integer hot counts")
    if after_hot >= before_hot and not owner_decision:
        raise StateProjectionError(
            "cleanup must reduce hot count or cite an explicit owner decision"
        )

    receipt_core: dict[str, Any] = {
        "schema": CLEANUP_RECEIPT_SCHEMA,
        "recorded_at": _now_text(now),
        "outcome": "owner_decision" if owner_decision else "reduction",
        "authorization_ref": authorization,
        "authorization_work_id": authorization_work_id,
        "owner_decision_ref": owner_decision or None,
        "before_sources": before_sources,
        "before_source_binding_digest": source_binding_digest,
        "after_sources": _receipt_sources(evaluation["sources"]),
        "before_hot_count": before_hot,
        "resulting_hot_count": after_hot,
        "active_work_digest": evaluation["active_work"]["digest"],
        "before_cleanup_plan": prior_plan,
        "cleanup_plan_digest": prior_plan_digest,
    }
    receipt = {
        **receipt_core,
        "receipt_digest": _canonical_digest(receipt_core),
    }
    payload = _projection_payload(
        evaluation,
        generated_at=str(receipt_core["recorded_at"]),
    )
    payload["cleanup_receipt"] = receipt
    _write_projection_payload(root, relative=relative, payload=payload)
    return evaluate_state(root, config=config)


def compact_summary(evaluation: dict[str, Any]) -> str:
    hot = evaluation.get("hot_count", 0)
    source_count = evaluation.get("source_count", 0)
    projection = evaluation.get("projection", {})
    source_debt = evaluation.get("source_debt", {})
    coverage = evaluation.get("active_coverage", {})
    cleanup = evaluation.get("cleanup_outcome", {})
    return (
        f"state={evaluation.get('state', 'unavailable')} "
        f"hot={hot} sources={source_count} "
        f"projection={projection.get('status', 'missing')} "
        f"debt={source_debt.get('status', 'unavailable')} "
        f"coverage={coverage.get('status', 'incomplete')} "
        f"cleanup={cleanup.get('status', 'none')} "
        f"readiness={evaluation.get('readiness', 'advisory')}"
    )
