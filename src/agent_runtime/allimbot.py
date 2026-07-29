"""Strict, optional producer boundary for native Allimbot project events.

Agent Runtime owns the event vocabulary and value policy.  Installed Allimbot
owns the durable SQLite spool and every delivery mechanism.  This module calls
``ProjectEmitter.emit`` only; it never flushes or sends an event over a network.
"""
from __future__ import annotations

import argparse
import functools
import importlib
import json
import math
import os
import re
import stat
import sys
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_SPEC = "allimbot.project/v1"
PROJECT_NAME = "agent-runtime"
PROJECT_SOURCE = "agent-runtime"
MAX_IDENTIFIER_LENGTH = 128
MAX_COUNT = 1_000_000
MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
_TASK_IDENTIFIER = re.compile(
    r"^TASK-[A-Z0-9]+(?:-[A-Z0-9]+)*$"
)
_ROLE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_SEMANTIC_RELEASE = re.compile(
    r"^v(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\."
    r"(?:0|[1-9][0-9]{0,3})(?:-(?:alpha|beta|rc)\."
    r"(?:0|[1-9][0-9]{0,3}))?$"
)
_SHA256_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ORG_MODEL_SCHEMA = "agent-runtime-org-model/v1"
_ORG_MODEL_MAX_BYTES = 128 * 1024
_ORG_MODEL_MAX_ENTRIES = 512
_ORG_MODEL_MAX_LIST_ITEMS = 512
_ORG_MODEL_TOP_LEVEL_KEYS = frozenset(
    {"schema", "updated_at", "tiers", "teams", "roles"}
)
_ORG_MODEL_TEAM_KEYS = frozenset({"id", "display_name"})
_ORG_MODEL_ROLE_KEYS = frozenset({"id", "tier", "team", "aliases"})
_ORG_MODEL_ALIAS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_SYSTEM_TASK_IDS = frozenset(
    {"agent-runtime", "owner-governance", "unscoped"}
)
_SYSTEM_OWNER_ROLES = frozenset({"owner", "runtime"})
_MANAGED_GATES = frozenset(
    {
        "attribution",
        "automation-rules",
        "collaboration-governance",
        "continuity-contract",
        "conversation-work-audit",
        "dependency-cycle",
        "design-system",
        "footprint-conflict",
        "knowledge-lint",
        "org-model",
        "owner-governance",
        "plan-assumption",
        "release-cadence",
        "release-council",
        "response-contract",
        "runtime-asset-usage",
        "scheduled-dispatch",
        "security-service",
        "state-machine",
        "state-sync",
        "task-identity",
        "taskset-boundary",
        "taskset-work",
        "verification-freshness",
        "work-schema",
        "worktree-lifecycle",
    }
)
_ATTENTION_KINDS = frozenset(
    {"governance-block", "legacy-notification", "runtime-update"}
)
_ATTENTION_STATES = frozenset({"attention", "available", "blocked"})
_TASK_STATES = frozenset(
    {
        "assigned",
        "attention",
        "available",
        "blocked",
        "claimed",
        "completed",
        "failed",
        "in-progress",
        "in_progress",
        "pending",
        "released",
        "review",
        "running",
        "waiting",
        "waiting-review",
        "waiting_review",
        "working",
    }
)
_TURN_RESULTS = frozenset({"blocked", "completed"})

MANAGED_RECIPE: dict[str, Any] = {
    "spec": PROJECT_SPEC,
    "project": PROJECT_NAME,
    "source": PROJECT_SOURCE,
    "events": {
        "attention.required": {
            "severity": "warning",
            "data_allowlist": [
                "task_id",
                "attention_kind",
                "owner_role",
                "state",
            ],
        },
        "task.state.changed": {
            "severity": "info",
            "data_allowlist": [
                "task_id",
                "from_state",
                "to_state",
                "owner_role",
            ],
        },
        "release.gate.failed": {
            "severity": "error",
            "data_allowlist": ["gate", "release", "finding_count"],
        },
        "turn.completed": {
            "severity": "info",
            "data_allowlist": [
                "task_id",
                "result_state",
                "duration_seconds",
            ],
        },
    },
}

_EVENT_FIELDS = {
    event_type: tuple(policy["data_allowlist"])
    for event_type, policy in MANAGED_RECIPE["events"].items()
}
_UNAVAILABLE_REASONS = frozenset(
    {
        "profile_not_selected",
        "dependency_missing",
        "dependency_unavailable",
        "dependency_incompatible",
        "configuration_unavailable",
        "spool_unavailable",
        "invalid_event_id",
    }
)

__all__ = [
    "EmitResult",
    "EventPolicyError",
    "MANAGED_RECIPE",
    "emit_event",
    "notify",
    "notify_on_complete",
]


class EventPolicyError(ValueError):
    """Raised before optional delivery when an event violates Runtime policy."""


@dataclass(frozen=True)
class EmitResult:
    """Bounded result that never contains exception, credential, or body text."""

    status: str
    event_id: str | None = None
    reason: str | None = None

    @property
    def spooled(self) -> bool:
        return self.status == "spooled"

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)

    def __bool__(self) -> bool:
        return self.spooled


def managed_recipe_path() -> Path:
    return Path(__file__).resolve().parent / "templates" / "project" / ".allimbot.json"


def _unavailable(reason: str) -> EmitResult:
    if reason not in _UNAVAILABLE_REASONS:
        reason = "dependency_unavailable"
    return EmitResult(status="unavailable", reason=reason)


def _load_managed_recipe(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EventPolicyError("managed Allimbot recipe is unavailable or malformed") from exc
    if payload != MANAGED_RECIPE:
        raise EventPolicyError("managed Allimbot recipe drift detected")
    return payload


def _regular_file(root: Path, relative: Path, field: str) -> Path:
    current = root
    parts = relative.parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise EventPolicyError(
                f"{field} is not registered in the Runtime repository"
            ) from exc
        final = index == len(parts) - 1
        if (
            stat.S_ISLNK(mode)
            or (final and not stat.S_ISREG(mode))
            or (not final and not stat.S_ISDIR(mode))
        ):
            raise EventPolicyError(
                f"{field} is not registered in the Runtime repository"
            )
    return current


def _task_id(value: object, root: Path | None) -> str:
    if not isinstance(value, str) or len(value) > MAX_IDENTIFIER_LENGTH:
        raise EventPolicyError("task_id must be a registered Runtime task identifier")
    if value in _SYSTEM_TASK_IDS:
        return value
    if _TASK_IDENTIFIER.fullmatch(value) is None or root is None:
        raise EventPolicyError("task_id must be a registered Runtime task identifier")
    _regular_file(
        root,
        Path("agents", "lead_engineer", "tasks", f"{value}.md"),
        "task_id",
    )
    return value


def _read_bounded_regular_file(path: Path, max_bytes: int) -> str:
    """Read one stable, non-symlink file snapshot without crossing the bound."""

    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise OSError("not a regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened_before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_before.st_mode)
            or (opened_before.st_dev, opened_before.st_ino)
            != (before.st_dev, before.st_ino)
            or opened_before.st_size > max_bytes
        ):
            raise OSError("file changed before it could be read")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(max_bytes + 1)
        opened_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    before_signature = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    opened_before_signature = (
        opened_before.st_dev,
        opened_before.st_ino,
        opened_before.st_mode,
        opened_before.st_size,
        opened_before.st_mtime_ns,
    )
    opened_after_signature = (
        opened_after.st_dev,
        opened_after.st_ino,
        opened_after.st_mode,
        opened_after.st_size,
        opened_after.st_mtime_ns,
    )
    after_signature = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if (
        len(payload) > max_bytes
        or before_signature != opened_before_signature
        or opened_before_signature != opened_after_signature
        or opened_after_signature != after_signature
    ):
        raise OSError("file changed while it was read")
    return payload.decode("utf-8")


def _org_inline_list(value: str, *, allow_empty: bool) -> tuple[str, ...]:
    if len(value) > 16 * 1024 or not value.startswith("[") or not value.endswith("]"):
        raise ValueError("unsupported inline list")
    body = value[1:-1]
    if not body.strip():
        if allow_empty and not body:
            return ()
        raise ValueError("empty inline list")
    raw_items = body.split(",")
    if len(raw_items) > _ORG_MODEL_MAX_LIST_ITEMS:
        raise ValueError("inline list exceeds bound")
    items = tuple(item.strip() for item in raw_items)
    if (
        any(_ORG_MODEL_ALIAS.fullmatch(item) is None for item in items)
        or len(items) != len(set(items))
    ):
        raise ValueError("invalid or duplicate inline-list item")
    return items


def _org_scalar(value: str) -> str:
    if (
        not 1 <= len(value) <= 128
        or value != value.strip()
        or any(ord(character) < 32 for character in value)
        or any(character in "[]{}#" for character in value)
    ):
        raise ValueError("invalid scalar")
    return value


def _parse_org_model(text: str) -> frozenset[str]:
    """Parse the deliberately small ORG-MODEL subset used for authorization."""

    if "\x00" in text or "\t" in text:
        raise ValueError("unsupported character")
    top: dict[str, object] = {}
    entries: dict[str, list[dict[str, object]]] = {"teams": [], "roles": []}
    section: str | None = None
    active: dict[str, object] | None = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        indentation = len(line) - len(line.lstrip(" "))
        if indentation == 0:
            match = re.fullmatch(r"([a-z_]+):(.*)", line)
            if match is None:
                raise ValueError("malformed top-level entry")
            key, raw_value = match.groups()
            if (
                key not in _ORG_MODEL_TOP_LEVEL_KEYS
                or key in top
                or (raw_value and not raw_value.startswith(" "))
            ):
                raise ValueError("unsupported or duplicate top-level entry")
            value = raw_value[1:] if raw_value else ""
            if key in {"teams", "roles"}:
                if value:
                    raise ValueError("list section must not have a scalar value")
                top[key] = entries[key]
                section = key
                active = None
            else:
                if not value:
                    raise ValueError("top-level scalar is missing")
                if key == "tiers":
                    top[key] = _org_inline_list(value, allow_empty=False)
                else:
                    top[key] = _org_scalar(value)
                section = None
                active = None
            continue

        if indentation == 2:
            if section not in entries:
                raise ValueError("list item is outside a supported section")
            match = re.fullmatch(r"  - id: ([a-z][a-z0-9-]{0,63})", line)
            if match is None:
                raise ValueError("unsupported nested or malformed list item")
            if len(entries[section]) >= _ORG_MODEL_MAX_ENTRIES:
                raise ValueError("section exceeds entry bound")
            active = {"id": match.group(1)}
            entries[section].append(active)
            continue

        if indentation == 4:
            if section not in entries or active is None:
                raise ValueError("property is outside a direct list item")
            match = re.fullmatch(r"    ([a-z_]+): (.+)", line)
            if match is None:
                raise ValueError("malformed list-item property")
            key, value = match.groups()
            allowed = (
                _ORG_MODEL_TEAM_KEYS
                if section == "teams"
                else _ORG_MODEL_ROLE_KEYS
            )
            if key == "id" or key not in allowed or key in active:
                raise ValueError("unsupported or duplicate list-item property")
            active[key] = (
                _org_inline_list(value, allow_empty=True)
                if key == "aliases"
                else _org_scalar(value)
            )
            continue

        raise ValueError("unsupported indentation")

    if set(top) != _ORG_MODEL_TOP_LEVEL_KEYS:
        raise ValueError("required top-level entry is missing")
    if top["schema"] != _ORG_MODEL_SCHEMA:
        raise ValueError("unsupported schema")
    tiers = top["tiers"]
    teams = entries["teams"]
    roles = entries["roles"]
    if (
        not isinstance(tiers, tuple)
        or not tiers
        or any(_ROLE_IDENTIFIER.fullmatch(tier) is None for tier in tiers)
        or not teams
        or not roles
        or any(set(team) != _ORG_MODEL_TEAM_KEYS for team in teams)
        or any(set(role) != _ORG_MODEL_ROLE_KEYS for role in roles)
    ):
        raise ValueError("registry contains an incomplete section or entry")

    team_ids = tuple(str(team["id"]) for team in teams)
    role_ids = tuple(str(role["id"]) for role in roles)
    if len(team_ids) != len(set(team_ids)) or len(role_ids) != len(set(role_ids)):
        raise ValueError("registry contains duplicate identifiers")
    tier_ids = frozenset(tiers)
    team_id_set = frozenset(team_ids)
    for role in roles:
        if role["tier"] not in tier_ids or role["team"] not in team_id_set:
            raise ValueError("role references an unregistered tier or team")
    return frozenset(role_ids)


def _registered_owner_roles(root: Path) -> frozenset[str]:
    registry = _regular_file(
        root,
        Path("agents", "project", "ORG-MODEL.yml"),
        "owner_role",
    )
    try:
        text = _read_bounded_regular_file(registry, _ORG_MODEL_MAX_BYTES)
        return _parse_org_model(text)
    except (OSError, UnicodeError, ValueError) as exc:
        raise EventPolicyError(
            "owner_role registry is unavailable or malformed"
        ) from exc


def _managed_value(
    value: object,
    field: str,
    allowed: frozenset[str],
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise EventPolicyError(f"{field} is outside the managed event vocabulary")
    return value


def _owner_role(value: object, root: Path | None) -> str:
    if not isinstance(value, str) or _ROLE_IDENTIFIER.fullmatch(value) is None:
        raise EventPolicyError("owner_role must be a registered Runtime role")
    if value in _SYSTEM_OWNER_ROLES:
        return value
    if root is None or value not in _registered_owner_roles(root):
        raise EventPolicyError("owner_role must be a registered Runtime role")
    return value


def _release(value: object) -> str:
    if not isinstance(value, str) or _SEMANTIC_RELEASE.fullmatch(value) is None:
        raise EventPolicyError("release must be a canonical semantic release tag")
    return value


def _uuid_value(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise EventPolicyError(f"{field} must be a canonical UUID")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError) as exc:
        raise EventPolicyError(f"{field} must be a canonical UUID") from exc
    if str(parsed) != value:
        raise EventPolicyError(f"{field} must be a canonical UUID")
    return value


def _dedupe_key(value: object) -> str:
    if not isinstance(value, str) or _SHA256_DIGEST.fullmatch(value) is None:
        raise EventPolicyError("dedupe_key must be a lowercase SHA-256 digest")
    return value


def _non_negative_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_COUNT:
        raise EventPolicyError(f"{field} must be a bounded non-negative integer")
    return value


def _duration(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EventPolicyError("duration_seconds must be a bounded non-negative number")
    converted = float(value)
    if not math.isfinite(converted) or not 0 <= converted <= MAX_DURATION_SECONDS:
        raise EventPolicyError("duration_seconds must be a bounded non-negative number")
    return value


def _validate_event(
    event_type: object,
    data: object,
    root: Path | None,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(event_type, str) or event_type not in _EVENT_FIELDS:
        raise EventPolicyError("event type is not enabled by the managed policy")
    if not isinstance(data, Mapping):
        raise EventPolicyError("event data must be an object")
    expected = set(_EVENT_FIELDS[event_type])
    provided = set(data)
    if provided != expected or any(not isinstance(key, str) for key in provided):
        raise EventPolicyError("event data fields do not match the managed policy")

    normalized: dict[str, Any] = {}
    for field in _EVENT_FIELDS[event_type]:
        value = data[field]
        if field == "finding_count":
            normalized[field] = _non_negative_integer(value, field)
        elif field == "duration_seconds":
            normalized[field] = _duration(value)
        elif field == "attention_kind":
            normalized[field] = _managed_value(value, field, _ATTENTION_KINDS)
        elif field == "state":
            normalized[field] = _managed_value(value, field, _ATTENTION_STATES)
        elif field in {"from_state", "to_state"}:
            normalized[field] = _managed_value(value, field, _TASK_STATES)
        elif field == "result_state":
            normalized[field] = _managed_value(value, field, _TURN_RESULTS)
        elif field == "owner_role":
            normalized[field] = _owner_role(value, root)
        elif field == "task_id":
            normalized[field] = _task_id(value, root)
        elif field == "gate":
            normalized[field] = _managed_value(value, field, _MANAGED_GATES)
        elif field == "release":
            normalized[field] = _release(value)
        else:
            raise EventPolicyError(f"{field} has no managed value contract")
    return event_type, normalized


def _summary(event_type: str, data: Mapping[str, Any]) -> str:
    if event_type == "attention.required":
        return (
            f"Attention required: {data['attention_kind']} [{data['state']}] "
            f"({data['task_id']}, owner={data['owner_role']})"
        )
    if event_type == "task.state.changed":
        return (
            f"Task {data['task_id']}: {data['from_state']} -> {data['to_state']} "
            f"(owner={data['owner_role']})"
        )
    if event_type == "release.gate.failed":
        return (
            f"Release {data['release']}: gate {data['gate']} failed "
            f"({data['finding_count']} findings)"
        )
    return (
        f"Turn completed for {data['task_id']}: {data['result_state']} "
        f"({float(data['duration_seconds']):g}s)"
    )


def _integration_matches(integration: object) -> bool:
    if (
        getattr(integration, "spec", None) != PROJECT_SPEC
        or getattr(integration, "project", None) != PROJECT_NAME
        or getattr(integration, "source", None) != PROJECT_SOURCE
    ):
        return False
    events = getattr(integration, "events", None)
    if not isinstance(events, Mapping) or set(events) != set(MANAGED_RECIPE["events"]):
        return False
    for event_type, expected in MANAGED_RECIPE["events"].items():
        policy = events[event_type]
        if (
            getattr(policy, "severity", None) != expected["severity"]
            or bool(getattr(policy, "sensitive", False))
            != bool(expected.get("sensitive", False))
            or tuple(getattr(policy, "data_allowlist", ()))
            != tuple(expected["data_allowlist"])
        ):
            return False
    return True


def emit_event(
    event_type: str,
    data: Mapping[str, Any],
    *,
    root: str | Path | None = None,
    recipe_path: str | Path | None = None,
    session_id: str | None = None,
    turn_id: str | None = None,
    dedupe_key: str | None = None,
) -> EmitResult:
    """Validate and enqueue one event through installed Allimbot.

    Policy violations raise :class:`EventPolicyError`.  Optional dependency,
    configuration, and spool failures return a bounded ``unavailable`` result.
    """

    resolved_root = Path(root).resolve() if root is not None else None
    normalized_type, normalized_data = _validate_event(
        event_type,
        data,
        resolved_root,
    )
    summary = _summary(normalized_type, normalized_data)
    if not 1 <= len(summary) <= 300:
        raise EventPolicyError("rendered event summary exceeds the managed bound")
    correlations = {
        "session_id": session_id,
        "turn_id": turn_id,
        "dedupe_key": dedupe_key,
    }
    for field, value in correlations.items():
        if value is not None:
            correlations[field] = (
                _dedupe_key(value)
                if field == "dedupe_key"
                else _uuid_value(value, field)
            )

    if recipe_path is not None:
        resolved_recipe = Path(recipe_path).resolve()
    elif resolved_root is not None:
        resolved_recipe = resolved_root / ".allimbot.json"
        if not resolved_recipe.is_file():
            return _unavailable("profile_not_selected")
    else:
        resolved_recipe = managed_recipe_path()
    _load_managed_recipe(resolved_recipe)

    try:
        integrations = importlib.import_module("allimbot.integrations")
    except ModuleNotFoundError as exc:
        reason = "dependency_missing" if exc.name in {"allimbot", "allimbot.integrations"} else "dependency_unavailable"
        return _unavailable(reason)
    except Exception:
        return _unavailable("dependency_unavailable")

    try:
        integration = integrations.ProjectIntegration.load(resolved_recipe)
    except Exception:
        # Distinguish a concurrently changed managed file (policy failure) from
        # an optional package whose integration API is incompatible.
        _load_managed_recipe(resolved_recipe)
        return _unavailable("dependency_incompatible")
    if not _integration_matches(integration):
        raise EventPolicyError("installed Allimbot integration disagrees with managed policy")

    try:
        emitter = integrations.ProjectEmitter(integration)
    except Exception:
        return _unavailable("configuration_unavailable")
    try:
        event_id = emitter.emit(
            normalized_type,
            summary,
            body="",
            data=normalized_data,
            session_id=correlations["session_id"],
            turn_id=correlations["turn_id"],
            dedupe_key=correlations["dedupe_key"],
        )
    except Exception:
        return _unavailable("spool_unavailable")
    try:
        normalized_event_id = _uuid_value(event_id, "event_id")
    except EventPolicyError:
        return _unavailable("invalid_event_id")
    return EmitResult(status="spooled", event_id=normalized_event_id)


def _legacy_event() -> EmitResult:
    return emit_event(
        "attention.required",
        {
            "task_id": "agent-runtime",
            "attention_kind": "legacy-notification",
            "owner_role": "owner",
            "state": "attention",
        },
    )


def notify(
    message: str,
    title: str = "agent_runtime",
    provider: str | None = None,
    timeout: float = 3.0,
) -> bool:
    """One-release compatibility signal; supplied free text is never forwarded."""

    del message, title, provider, timeout
    return bool(_legacy_event())


def notify_on_complete(
    title: str | None = None,
    provider: str | None = None,
) -> Callable:
    """Decorate a function with secret-free structured state transitions."""

    del title, provider

    def decorator(function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = function(*args, **kwargs)
            except Exception:
                try:
                    emit_event(
                        "task.state.changed",
                        {
                            "task_id": "agent-runtime",
                            "from_state": "running",
                            "to_state": "failed",
                            "owner_role": "runtime",
                        },
                    )
                except Exception:
                    pass
                raise
            try:
                emit_event(
                    "task.state.changed",
                    {
                        "task_id": "agent-runtime",
                        "from_state": "running",
                        "to_state": "completed",
                        "owner_role": "runtime",
                    },
                )
            except Exception:
                pass
            return result

        return wrapper

    return decorator


def _stdin_payload() -> dict[str, Any]:
    try:
        payload = json.loads(sys.stdin.read())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EventPolicyError("structured event input must be a JSON object") from exc
    if not isinstance(payload, dict):
        raise EventPolicyError("structured event input must be a JSON object")
    allowed = {
        "event_type",
        "data",
        "session_id",
        "turn_id",
        "dedupe_key",
    }
    if set(payload) - allowed:
        raise EventPolicyError("structured event input contains unexpected fields")
    return payload


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enqueue a strict native Allimbot project event")
    parser.add_argument("message", nargs="?", help="legacy message (ignored)")
    parser.add_argument("-t", "--title", default="agent_runtime", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--provider", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--stdin", action="store_true", help="read structured event JSON from stdin")
    parser.add_argument("--json", action="store_true", help="print a bounded result object")
    args = parser.parse_args(argv)

    try:
        if args.stdin:
            payload = _stdin_payload()
            result = emit_event(
                payload.get("event_type"),
                payload.get("data"),
                root=args.root,
                session_id=payload.get("session_id"),
                turn_id=payload.get("turn_id"),
                dedupe_key=payload.get("dedupe_key"),
            )
        elif args.message is not None:
            # Do not pass any positional/title/provider content into the event.
            result = _legacy_event()
        else:
            parser.error("provide --stdin or a legacy positional message")
    except EventPolicyError:
        if args.json:
            print(json.dumps({"status": "rejected", "reason": "policy_error"}))
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
