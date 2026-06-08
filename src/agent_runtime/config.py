from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CONFIG_FILE = "agent_runtime.yml"
LEGACY_CONFIG_FILE = "ralph.yml"


@dataclass(frozen=True)
class AgentRuntimeConfig:
    project: str
    sync_mode: str
    allow_silent_overwrite: bool
    path: Path
    upstream_package: str = ""
    upstream_remote_url: str = ""
    upstream_ref: str = ""
    unmanaged_paths: tuple[str, ...] = ()


RalphConfig = AgentRuntimeConfig


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1", "on"}:
        return True
    if normalized in {"false", "no", "0", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def config_path(root: Path) -> Path:
    primary = root / CONFIG_FILE
    if primary.exists():
        return primary
    legacy = root / LEGACY_CONFIG_FILE
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"{CONFIG_FILE} not found under {root}")


def load_config(root: Path) -> AgentRuntimeConfig:
    path = config_path(root)

    project = ""
    sync_mode = ""
    allow_silent_overwrite: bool | None = None
    upstream_package = ""
    upstream_remote_url = ""
    upstream_ref = ""
    unmanaged_paths: list[str] = []
    section = ""
    list_key = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent > 0 and line.startswith("- ") and section == "sync" and list_key == "unmanaged":
            unmanaged_paths.append(line.removeprefix("- ").strip().strip("\"'").replace("\\", "/"))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if indent == 0:
            section = key if not value else ""
            list_key = ""
            if key == "project":
                project = value
            continue

        list_key = key if not value else ""
        if section == "sync" and key == "mode":
            sync_mode = value
        elif section == "sync" and key == "allow_silent_overwrite":
            allow_silent_overwrite = _parse_bool(value)
        elif section == "upstream" and key == "package":
            upstream_package = value
        elif section == "upstream" and key == "remote_url":
            upstream_remote_url = value
        elif section == "upstream" and key == "ref":
            upstream_ref = value

    if not project:
        raise ValueError(f"{path} is missing project")
    if not sync_mode:
        raise ValueError(f"{path} is missing sync.mode")
    if allow_silent_overwrite is None:
        raise ValueError(f"{path} is missing sync.allow_silent_overwrite")

    return AgentRuntimeConfig(
        project=project,
        sync_mode=sync_mode,
        allow_silent_overwrite=allow_silent_overwrite,
        path=path,
        upstream_package=upstream_package,
        upstream_remote_url=upstream_remote_url,
        upstream_ref=upstream_ref,
        unmanaged_paths=tuple(path for path in unmanaged_paths if path),
    )
