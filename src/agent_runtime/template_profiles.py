from __future__ import annotations

"""Fail-closed profile selection for the packaged host template."""

import fnmatch
import json
from pathlib import Path

MANIFEST_RELATIVE = "agents/project/RUNTIME-PROFILE-MANIFEST.json"
SCHEMA = "agent-runtime-template-profiles/v1"


def load_manifest(template_root: Path) -> dict:
    path = template_root / MANIFEST_RELATIVE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid template profile manifest: {exc}") from exc
    if data.get("schema") != SCHEMA or not isinstance(data.get("profiles"), dict):
        raise ValueError("invalid template profile manifest schema")
    return data


def selected_paths(template_root: Path, profiles: tuple[str, ...]) -> tuple[Path, ...]:
    manifest = load_manifest(template_root)
    declared = manifest["profiles"]
    requested = ("core", *[profile for profile in profiles if profile != "core"])
    if any(profile not in declared for profile in requested):
        raise ValueError("unknown template profile")
    files = sorted((path for path in template_root.rglob("*") if path.is_file()), key=lambda path: path.relative_to(template_root).as_posix())
    selected: set[Path] = set()
    for profile in requested:
        rules = declared[profile]
        for path in files:
            rel = path.relative_to(template_root).as_posix()
            if any(fnmatch.fnmatch(rel, pattern) for pattern in rules.get("include", [])):
                selected.add(path)
            if any(fnmatch.fnmatch(rel, pattern) for pattern in rules.get("exclude", [])):
                selected.discard(path)
    return tuple(sorted(selected, key=lambda path: path.relative_to(template_root).as_posix().lower()))
