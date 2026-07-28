from __future__ import annotations

"""The deliberately small Agent Runtime configuration reader.

The runtime has no YAML dependency.  This module therefore supports the
documented configuration shapes only: scalar mappings, indented mappings and
scalar lists.  Keeping that boundary explicit makes a malformed host config a
visible blocker rather than silently accepting a YAML feature we do not own.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_FILE = "agent_runtime.yml"
LEGACY_CONFIG_FILE = "ralph.yml"
V1_SCHEMA = "agent-runtime-config/v1"
V2_SCHEMA = "agent-runtime-config/v2"
EFFECTIVE_SCHEMA = V2_SCHEMA
HOST_CONTEXT_SCHEMA = "host-context/v1"
CANONICAL_HOST_CONTEXT = "agents/host/HOST-CONTEXT.yml"

PROFILE_ORDER = ("core", "web-content", "security-service")
PROFILE_CAPABILITIES = {
    "core": ("lifecycle", "continuity", "verification", "compound", "scribe", "model-routing"),
    "web-content": ("web-content",),
    "security-service": ("security-service",),
}
CAPABILITY_ORDER = tuple(capability for profile in PROFILE_ORDER for capability in PROFILE_CAPABILITIES[profile])
OWNERSHIP_MODES = ("managed", "seed_once", "host_owned", "generated")
RESERVED_PATHS = {CONFIG_FILE, "agent_runtime.lock.json"}


@dataclass(frozen=True)
class HostContext:
    path: str = CANONICAL_HOST_CONTEXT
    present: bool = False
    purpose: str = ""
    domain: str = ""
    safety_constraints: tuple[str, ...] = ()
    role_mapping: tuple[tuple[str, str], ...] = ()
    read_more: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentRuntimeConfig:
    # Existing v1 public fields.  Keep these first and keep unmanaged_paths
    # byte-compatible for sync.py and lock.py.
    project: str
    sync_mode: str
    allow_silent_overwrite: bool
    path: Path
    upstream_package: str = ""
    upstream_remote_url: str = ""
    upstream_ref: str = ""
    unmanaged_paths: tuple[str, ...] = ()
    # v2 effective projection.
    source_schema: str = V1_SCHEMA
    effective_schema: str = EFFECTIVE_SCHEMA
    profiles: tuple[str, ...] = ("core", "web-content", "security-service")
    capabilities: tuple[str, ...] = CAPABILITY_ORDER
    ownership: tuple[tuple[str, tuple[str, ...]], ...] = ()
    host_context: HostContext = HostContext()
    role_overlay: str = ""
    risk_paths: tuple[str, ...] = ()
    state_adapters: tuple[tuple[str, str], ...] = ()

    def ownership_for(self, mode: str) -> tuple[str, ...]:
        return dict(self.ownership).get(mode, ())


RalphConfig = AgentRuntimeConfig


def _parse_bool(value: object) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1", "on"}:
        return True
    if normalized in {"false", "no", "0", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def _strip_comment(value: str) -> str:
    for index, char in enumerate(value):
        if char == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value.rstrip()


def _scalar(value: str) -> str:
    value = value.strip()
    if value[:1] not in {"\"", "'"}:
        return _strip_comment(value).strip()
    quote = value[0]
    end = value.find(quote, 1)
    if end < 0:
        raise ValueError(f"malformed quoted scalar: {value!r}")
    trailing = value[end + 1 :]
    if trailing and not trailing[0].isspace():
        raise ValueError(f"malformed quoted scalar: {value!r}")
    if trailing.strip() and not trailing.lstrip().startswith("#"):
        raise ValueError(f"malformed quoted scalar: {value!r}")
    return value[1:end]


def _parse_document(path: Path) -> dict[str, Any]:
    """Parse the bounded YAML subset used by v1/v2 and host-context/v1."""
    lines: list[tuple[int, str]] = []
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    for raw in raw_lines:
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError(f"{path} uses tabs for indentation")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines) or lines[index][0] < indent:
            return {}, index
        is_list = lines[index][0] == indent and lines[index][1].startswith("- ")
        result: Any = [] if is_list else {}
        while index < len(lines):
            line_indent, line = lines[index]
            if line_indent < indent:
                break
            if line_indent != indent:
                raise ValueError(f"{path} has unexpected indentation near: {line}")
            if is_list:
                if not line.startswith("- "):
                    raise ValueError(f"{path} mixes list and mapping entries")
                item = _scalar(line[2:])
                if not item:
                    raise ValueError(f"{path} has an empty list item")
                result.append(item)
                index += 1
                continue
            if line.startswith("- ") or ":" not in line:
                raise ValueError(f"{path} has unsupported YAML syntax near: {line}")
            key, raw_value = line.split(":", 1)
            key = key.strip()
            if not key or key in result:
                raise ValueError(f"{path} has duplicate or empty key: {key!r}")
            value = _scalar(raw_value)
            index += 1
            if value in {">", ">-", "|", "|-"}:
                folded: list[str] = []
                while index < len(lines) and lines[index][0] > indent:
                    folded.append(lines[index][1])
                    index += 1
                if not folded:
                    raise ValueError(f"{path} has empty folded scalar for {key}")
                result[key] = " ".join(folded) if value.startswith(">") else "\n".join(folded)
            elif value:
                result[key] = value
            elif index < len(lines) and lines[index][0] > indent:
                result[key], index = parse_block(index, lines[index][0])
            else:
                result[key] = {}
        return result, index

    if not lines:
        return {}
    if lines[0][0] != 0:
        raise ValueError(f"{path} must contain a zero-indented top-level mapping")
    parsed, index = parse_block(0, 0)
    if index != len(lines) or not isinstance(parsed, dict):
        raise ValueError(f"{path} must contain a top-level mapping")
    return parsed


def _as_mapping(value: object, name: str, path: Path) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} {name} must be a mapping")
    return value


def _as_list(value: object, name: str, path: Path) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path} {name} must be a scalar list")
    return value


def _scalar_value(value: object, name: str, path: Path) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} {name} must be a scalar string")
    return value


def _normal_path(value: object, name: str, path: Path, *, allow_trailing_slash: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} {name} must be a path string")
    raw = value.strip()
    if allow_trailing_slash:
        raw = raw.rstrip("/")
    if not raw or "\\" in raw or raw.startswith("/") or raw.startswith("~") or (len(raw) >= 2 and raw[1] == ":"):
        raise ValueError(f"{path} {name} is not a safe repo-relative POSIX path: {value!r}")
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts) or parts[0] == ".git":
        raise ValueError(f"{path} {name} is not a safe repo-relative POSIX path: {value!r}")
    normalized = "/".join(parts)
    if normalized in RESERVED_PATHS:
        raise ValueError(f"{path} {name} cannot classify runtime config or lock file")
    return normalized


def _unique(items: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _profiles(value: object, path: Path, source_schema: str) -> tuple[str, ...]:
    requested = _as_list(value, "profiles", path) if value is not None else ([] if source_schema == V2_SCHEMA else ["full-runtime"])
    if source_schema == V2_SCHEMA and not requested:
        requested = ["core"]
    requested = list(_unique(requested))
    if "full-runtime" in requested:
        if len(requested) != 1:
            raise ValueError(f"{path} profiles full-runtime cannot be combined with another profile")
        return PROFILE_ORDER
    unknown = sorted(set(requested) - set(PROFILE_ORDER))
    if unknown:
        raise ValueError(f"{path} has unknown profile identifiers: {', '.join(unknown)}")
    requested.append("core")
    return tuple(profile for profile in PROFILE_ORDER if profile in requested)


def _capabilities(profiles: tuple[str, ...], value: object, path: Path) -> tuple[str, ...]:
    requested = _as_list(value, "capabilities", path)
    allowed = set(CAPABILITY_ORDER)
    unknown = sorted(set(requested) - allowed)
    if unknown:
        raise ValueError(f"{path} has unknown capability identifiers: {', '.join(unknown)}")
    enabled = set(requested)
    for profile in profiles:
        enabled.update(PROFILE_CAPABILITIES[profile])
    return tuple(capability for capability in CAPABILITY_ORDER if capability in enabled)


def _ownership(value: object, unmanaged: tuple[str, ...], path: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    mapping = _as_mapping(value, "ownership", path)
    unknown = sorted(set(mapping) - set(OWNERSHIP_MODES))
    if unknown:
        raise ValueError(f"{path} has unknown ownership modes: {', '.join(unknown)}")
    by_mode: dict[str, tuple[str, ...]] = {}
    classified: list[tuple[str, str]] = []
    for mode in OWNERSHIP_MODES:
        values = [_normal_path(item, f"ownership.{mode}", path) for item in _as_list(mapping.get(mode), f"ownership.{mode}", path)]
        if mode == "host_owned":
            values.extend(unmanaged)
        values = list(_unique(values))
        for item in values:
            if (item == "agents/host" or item.startswith("agents/host/")) and mode != "host_owned":
                raise ValueError(f"{path} agents/host paths may only be host_owned: {item}")
            classified.append((item, mode))
        by_mode[mode] = tuple(values)
    for index, (left, left_mode) in enumerate(classified):
        for right, right_mode in classified[index + 1 :]:
            if left_mode == right_mode:
                continue
            if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
                raise ValueError(f"{path} has mixed ownership overlap: {left} ({left_mode}) vs {right} ({right_mode})")
    return tuple((mode, by_mode[mode]) for mode in OWNERSHIP_MODES)


def _read_host_context(root: Path, host: dict[str, Any], path: Path) -> tuple[HostContext, str, tuple[str, ...], tuple[tuple[str, str], ...]]:
    unknown_host = sorted(set(host) - {"context", "role_overlay", "risk_paths", "state_adapters"})
    if unknown_host:
        raise ValueError(f"{path} host has unknown keys: {', '.join(unknown_host)}")
    context_path = host.get("context", CANONICAL_HOST_CONTEXT)
    if context_path != CANONICAL_HOST_CONTEXT:
        raise ValueError(f"{path} host.context must be {CANONICAL_HOST_CONTEXT}")
    role_overlay = _normal_path(host["role_overlay"], "host.role_overlay", path) if "role_overlay" in host else ""
    risk_paths = tuple(_normal_path(item, "host.risk_paths", path, allow_trailing_slash=True) for item in _as_list(host.get("risk_paths"), "host.risk_paths", path))
    adapters = _as_mapping(host.get("state_adapters"), "host.state_adapters", path)
    state_adapters = tuple(sorted((key, _normal_path(value, f"host.state_adapters.{key}", path)) for key, value in adapters.items()))
    context_file = root / CANONICAL_HOST_CONTEXT
    if not context_file.exists():
        return HostContext(), role_overlay, _unique(list(risk_paths)), state_adapters
    document = _parse_document(context_file)
    schema = document.get("schema", "")
    if schema != HOST_CONTEXT_SCHEMA:
        raise ValueError(f"{context_file} must declare schema: {HOST_CONTEXT_SCHEMA}")
    allowed = {"schema", "purpose", "domain", "safety_constraints", "role_mapping", "read_more"}
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise ValueError(f"{context_file} has unknown keys: {', '.join(unknown)}")
    role_mapping = _as_mapping(document.get("role_mapping"), "role_mapping", context_file)
    purpose = _scalar_value(document.get("purpose", ""), "purpose", context_file)
    domain = _scalar_value(document.get("domain", ""), "domain", context_file)
    if any(not isinstance(value, str) for value in role_mapping.values()):
        raise ValueError(f"{context_file} role_mapping values must be scalar strings")
    read_more = tuple(_normal_path(item, "read_more", context_file) for item in _as_list(document.get("read_more"), "read_more", context_file))
    return (
        HostContext(
            present=True,
            purpose=purpose,
            domain=domain,
            safety_constraints=_unique(_as_list(document.get("safety_constraints"), "safety_constraints", context_file)),
            role_mapping=tuple(sorted(role_mapping.items())),
            read_more=_unique(list(read_more)),
        ),
        role_overlay,
        _unique(list(risk_paths)),
        state_adapters,
    )


def config_path(root: Path) -> Path:
    primary = root / CONFIG_FILE
    if primary.exists():
        return primary
    legacy = root / LEGACY_CONFIG_FILE
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"{CONFIG_FILE} not found under {root}")


def load_config(root: Path) -> AgentRuntimeConfig:
    root = root.resolve()
    path = config_path(root)
    document = _parse_document(path)
    explicit_schema = "schema" in document
    source_schema = document.get("schema", V1_SCHEMA)
    if explicit_schema and source_schema != V2_SCHEMA:
        raise ValueError(f"{path} has unsupported schema: {source_schema}")
    allowed_root = {"project", "upstream", "sync"} if not explicit_schema else {
        "schema", "project", "upstream", "sync", "profiles", "capabilities", "ownership", "host"
    }
    unknown_root = sorted(set(document) - allowed_root)
    if unknown_root:
        raise ValueError(f"{path} has unknown root keys: {', '.join(unknown_root)}")
    project = _scalar_value(document.get("project", ""), "project", path).strip()
    sync = _as_mapping(document.get("sync"), "sync", path)
    allowed_sync = {"mode", "allow_silent_overwrite", "unmanaged"}
    unknown_sync = sorted(set(sync) - allowed_sync)
    if unknown_sync:
        raise ValueError(f"{path} sync has unknown keys: {', '.join(unknown_sync)}")
    sync_mode = _scalar_value(sync.get("mode", ""), "sync.mode", path).strip()
    if not project:
        raise ValueError(f"{path} is missing project")
    if not sync_mode:
        raise ValueError(f"{path} is missing sync.mode")
    if "allow_silent_overwrite" not in sync:
        raise ValueError(f"{path} is missing sync.allow_silent_overwrite")
    if explicit_schema and "unmanaged" in sync:
        raise ValueError(f"{path} v2 sync.unmanaged is unsupported; use ownership.host_owned")
    unmanaged = tuple(
        _normal_path(item.replace("\\", "/"), "sync.unmanaged", path)
        for item in _as_list(sync.get("unmanaged"), "sync.unmanaged", path)
    )
    upstream = _as_mapping(document.get("upstream"), "upstream", path)
    unknown_upstream = sorted(set(upstream) - {"package", "remote_url", "ref"})
    if unknown_upstream:
        raise ValueError(f"{path} upstream has unknown keys: {', '.join(unknown_upstream)}")
    for key, value in upstream.items():
        _scalar_value(value, f"upstream.{key}", path)
    host = _as_mapping(document.get("host"), "host", path)
    profiles = _profiles(document.get("profiles"), path, source_schema)
    context, role_overlay, risk_paths, state_adapters = _read_host_context(root, host, path)
    return AgentRuntimeConfig(
        project=project,
        sync_mode=sync_mode,
        allow_silent_overwrite=_parse_bool(sync["allow_silent_overwrite"]),
        path=path,
        upstream_package=_scalar_value(upstream.get("package", ""), "upstream.package", path),
        upstream_remote_url=_scalar_value(upstream.get("remote_url", ""), "upstream.remote_url", path),
        upstream_ref=_scalar_value(upstream.get("ref", ""), "upstream.ref", path),
        unmanaged_paths=unmanaged,
        source_schema=source_schema,
        profiles=profiles,
        capabilities=_capabilities(profiles, document.get("capabilities"), path),
        ownership=_ownership(document.get("ownership"), unmanaged, path),
        host_context=context,
        role_overlay=role_overlay,
        risk_paths=risk_paths,
        state_adapters=state_adapters,
    )
