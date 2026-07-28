from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import __version__
from .config import CONFIG_FILE
from .config import AgentRuntimeConfig
from .config import LEGACY_CONFIG_FILE
from .config import load_config
from .publish_check import PublishFinding
from .sync import _content_digest
from .sync import _ownership
from .sync import build_sync_plan
from .sync import _template_files
from .sync import default_template_root
from .sync import template_digest


@dataclass(frozen=True)
class AgentRuntimeLockPlan:
    root: Path
    config: AgentRuntimeConfig
    lock_path: Path
    template_root: Path
    record: dict[str, Any]
    findings: tuple[PublishFinding, ...] = ()


LOCK_FILE = "agent_runtime.lock.json"
LEGACY_LOCK_FILE = "ralph.lock.json"


def _template_digest(template_root: Path, unmanaged_paths: tuple[str, ...] = ()) -> tuple[str, int]:
    # Compatibility wrapper; v2 uses the single sync canonical digest.
    if not unmanaged_paths:
        return template_digest(template_root)
    digest = hashlib.sha256()
    files = [path for path in _template_files(template_root) if path.relative_to(template_root).as_posix() not in set(unmanaged_paths)]
    for path in files:
        digest.update(path.relative_to(template_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_content(path))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}", len(files)


def _managed_files(template_root: Path, unmanaged_paths: tuple[str, ...] = ()) -> dict[str, str]:
    unmanaged = set(unmanaged_paths)
    return {
        path.relative_to(template_root).as_posix(): _content_digest(path)
        for path in _template_files(template_root)
        if path.relative_to(template_root).as_posix() not in unmanaged
    }


def _canonical_content(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def build_lock_record(root: Path, template_root: Path | None = None) -> dict[str, Any]:
    config = load_config(root)
    resolved_template_root = template_root or default_template_root()
    plan = build_sync_plan(root, template_root=resolved_template_root)
    ownership = {path.relative_to(resolved_template_root).as_posix(): _ownership(config, path.relative_to(resolved_template_root).as_posix()) for path in _template_files(resolved_template_root)}
    managed = {path: digest for path, digest in _managed_files(resolved_template_root).items() if ownership[path] == "managed"}
    digest, file_count = template_digest(resolved_template_root)
    seeded = sorted(item.path for item in plan.preserved if item.ownership == "seed_once")
    return {
        "schema": "agent-runtime-lock/v2",
        "project": config.project,
        "profiles": list(config.profiles),
        "capabilities": list(config.capabilities),
        "upstream": {
            "package": config.upstream_package,
            "remote_url": config.upstream_remote_url,
            "ref": config.upstream_ref,
        },
        "installed": {
            "package_version": __version__,
            "template_digest": digest,
            "template_files": file_count,
            "ownership": dict(sorted(ownership.items())),
            "managed_files": dict(sorted(managed.items())),
            "seeded": seeded,
        },
    }


def _load_existing_lock(root: Path) -> tuple[Path, dict[str, Any]] | None:
    for name in (LOCK_FILE, LEGACY_LOCK_FILE):
        path = root / name
        if path.exists():
            return path, json.loads(path.read_text(encoding="utf-8"))
    return None


def build_lock_plan(root: Path, template_root: Path | None = None) -> AgentRuntimeLockPlan:
    resolved_root = root.resolve()
    resolved_template_root = (template_root or default_template_root()).resolve()
    config = load_config(resolved_root)
    lock_path = resolved_root / LOCK_FILE
    record = build_lock_record(resolved_root, template_root=resolved_template_root)
    findings: list[PublishFinding] = []

    if not config.upstream_remote_url:
        findings.append(PublishFinding(CONFIG_FILE, "missing-upstream-remote-url", "upstream.remote_url is required"))
    if not config.upstream_ref:
        findings.append(PublishFinding(CONFIG_FILE, "missing-upstream-ref", "upstream.ref is required"))

    try:
        existing_pair = _load_existing_lock(resolved_root)
    except json.JSONDecodeError as exc:
        findings.append(PublishFinding(LOCK_FILE, "malformed-lock-file", str(exc)))
        existing = None
    else:
        existing = existing_pair[1] if existing_pair else None

    if existing is None:
        findings.append(PublishFinding(LOCK_FILE, "missing-lock-file", "run agent_runtime lock --write"))
    elif existing != record:
        findings.append(PublishFinding(LOCK_FILE, "lock-out-of-date", "run agent_runtime lock --write"))

    return AgentRuntimeLockPlan(
        root=resolved_root,
        config=config,
        lock_path=lock_path,
        template_root=resolved_template_root,
        record=record,
        findings=tuple(findings),
    )


def write_lock(plan: AgentRuntimeLockPlan) -> None:
    plan.lock_path.write_text(json.dumps(plan.record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render(plan: AgentRuntimeLockPlan) -> str:
    installed = plan.record["installed"]
    upstream = plan.record["upstream"]
    lines = [
        "# Agent Runtime Lock",
        "",
        f"project={plan.config.project}",
        f"lock_path={plan.lock_path}",
        f"upstream_package={upstream['package']}",
        f"upstream_remote_url={upstream['remote_url']}",
        f"upstream_ref={upstream['ref']}",
        f"package_version={installed['package_version']}",
        f"template_digest={installed['template_digest']}",
        f"template_files={installed['template_files']}",
        f"findings={len(plan.findings)}",
    ]
    if plan.findings:
        lines.extend(["", "## Findings", ""])
        for finding in plan.findings:
            lines.append(f"- `{finding.path}` {finding.kind}: {finding.detail}")
    return "\n".join(lines)


def _write_blockers(findings: tuple[PublishFinding, ...]) -> tuple[PublishFinding, ...]:
    return tuple(
        finding
        for finding in findings
        if finding.kind in {"missing-upstream-remote-url", "missing-upstream-ref"}
    )


def run_lock(root: Path, *, mode: str, template_root: Path | None = None) -> int:
    plan = build_lock_plan(root, template_root=template_root)
    if mode == "write":
        blockers = _write_blockers(plan.findings)
        if build_sync_plan(root, template_root=template_root).conflicts:
            print(render(plan))
            print("lock write refused: unresolved sync conflicts")
            return 1
        if blockers:
            print(render(plan))
            return 1
        write_lock(plan)
        plan = build_lock_plan(root, template_root=template_root)
        print(render(plan))
        return 1 if plan.findings else 0
    if mode == "check":
        print(render(plan))
        return 1 if plan.findings else 0
    raise ValueError(f"unknown lock mode: {mode}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check or write the host Agent Runtime upstream lock")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Host project root")
    parser.add_argument("--template-root", type=Path, default=None, help="Template root override")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help=f"Fail if {LOCK_FILE} is missing or stale")
    mode.add_argument("--write", action="store_true", help=f"Write {LOCK_FILE} for the current installed package")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_lock(args.root, mode="write" if args.write else "check", template_root=args.template_root)


if __name__ == "__main__":
    raise SystemExit(main())
