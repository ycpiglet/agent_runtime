from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import AgentRuntimeConfig, load_config

LOCK_FILE = "agent_runtime.lock.json"
LEGACY_LOCK_FILE = "ralph.lock.json"


@dataclass(frozen=True)
class TemplateUpdate:
    path: str
    action: str
    source: Path
    target: Path
    ownership: str = "managed"
    reason: str = ""
    safety: str = "safe"


@dataclass(frozen=True)
class SyncPlan:
    root: Path
    config: AgentRuntimeConfig
    template_root: Path
    updates: tuple[TemplateUpdate, ...] = ()
    conflicts: tuple[TemplateUpdate, ...] = ()
    preserved: tuple[TemplateUpdate, ...] = ()
    excluded: tuple[TemplateUpdate, ...] = ()
    lock_schema: str = "none"
    prior_managed: tuple[str, ...] = ()
    seeded: tuple[str, ...] = ()


def default_template_root() -> Path:
    return Path(__file__).resolve().parent / "templates" / "project"


def _is_runtime_artifact(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def _template_files(template_root: Path) -> list[Path]:
    if not template_root.exists():
        return []
    return sorted(
        (path for path in template_root.rglob("*") if path.is_file() and not _is_runtime_artifact(path)),
        key=lambda path: path.relative_to(template_root).as_posix().lower(),
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _canonical_content(path: Path) -> bytes:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _content_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(_canonical_content(path)).hexdigest()}"


def _load_lock(root: Path) -> dict[str, object]:
    lock_path = root / LOCK_FILE
    if not lock_path.exists():
        lock_path = root / LEGACY_LOCK_FILE
    if not lock_path.exists():
        return {}
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_managed_files(root: Path) -> dict[str, str]:
    data = _load_lock(root)
    managed = data.get("installed", {}).get("managed_files", {})
    if not isinstance(managed, dict):
        return {}
    return {str(path): str(digest) for path, digest in managed.items()}


def _ownership(config: AgentRuntimeConfig, path: str) -> str:
    for mode, paths in config.ownership:
        if any(path == candidate or path.startswith(candidate.rstrip("/") + "/") for candidate in paths):
            return mode
    if path in {"AGENTS.md", "CLAUDE.md", "CURSOR.md", "GEMINI.md", "agents/project/NEXT-SESSION-POINTER.yml"}:
        return "seed_once"
    return "managed"


def build_sync_plan(root: Path, template_root: Path | None = None) -> SyncPlan:
    config = load_config(root)
    try:
        resolved_template_root = Path(template_root) if template_root is not None else default_template_root()
    except TypeError as exc:
        raise TypeError("template_root must be path-like") from exc
    lock = _load_lock(root)
    managed_files = _load_managed_files(root)
    installed = lock.get("installed", {}) if isinstance(lock.get("installed", {}), dict) else {}
    seeded = {str(path) for path in installed.get("seeded", [])} if isinstance(installed.get("seeded", []), list) else set()
    updates: list[TemplateUpdate] = []
    conflicts: list[TemplateUpdate] = []
    preserved: list[TemplateUpdate] = []
    excluded: list[TemplateUpdate] = []
    for source in _template_files(resolved_template_root):
        rel = source.relative_to(resolved_template_root).as_posix()
        ownership = _ownership(config, rel)
        target = root / rel
        if ownership in {"host_owned", "generated"}:
            excluded.append(TemplateUpdate(rel, "excluded", source, target, ownership, "owner-controlled path", "never"))
            continue
        if target.is_symlink() or (target.exists() and not target.is_file()):
            conflicts.append(TemplateUpdate(rel, "conflict", source, target, ownership, "non-regular target", "unsafe"))
            continue
        if ownership == "seed_once":
            if target.exists():
                preserved.append(TemplateUpdate(rel, "preserve", source, target, ownership, "existing seed", "never"))
            elif rel in seeded or rel in managed_files:
                preserved.append(TemplateUpdate(rel, "preserve", source, target, ownership, "prior seed evidence", "never"))
            else:
                updates.append(TemplateUpdate(rel, "seed", source, target, ownership, "first installation", "safe"))
            continue
        update = TemplateUpdate(rel, "create", source, target, ownership, "missing target", "safe")
        if not target.exists():
            updates.append(update)
            continue
        if _read(source) == _read(target):
            preserved.append(TemplateUpdate(rel, "identical", source, target, ownership, "matches template", "never"))
            continue
        if managed_files.get(rel) == _content_digest(target):
            updates.append(TemplateUpdate(rel, "update", source, target, ownership, "matches prior managed digest", "safe"))
            continue
        conflicts.append(TemplateUpdate(rel, "conflict", source, target, ownership, "host content differs", "unsafe"))
    return SyncPlan(
        root=root,
        config=config,
        template_root=resolved_template_root,
        updates=tuple(updates),
        conflicts=tuple(conflicts),
        preserved=tuple(preserved), excluded=tuple(excluded), lock_schema=str(lock.get("schema", "none")),
        prior_managed=tuple(sorted(managed_files)), seeded=tuple(sorted(seeded)),
    )


def render_check(plan: SyncPlan) -> str:
    status = "blocked" if plan.config.allow_silent_overwrite else "ready"
    lines = [
        "# Agent Runtime Sync Check",
        "",
        f"project={plan.config.project}",
        f"mode={plan.config.sync_mode}",
        f"allow_silent_overwrite={str(plan.config.allow_silent_overwrite).lower()}",
        f"status={status}",
        f"updates={len(plan.updates)}",
        f"conflicts={len(plan.conflicts)}",
    ]
    for update in plan.updates:
        lines.append(f"- {update.action} {update.path}")
    for conflict in plan.conflicts:
        lines.append(f"- conflict {conflict.path}")
    return "\n".join(lines)


def reconcile_json(plan: SyncPlan) -> str:
    actions = sorted([*plan.updates, *plan.conflicts, *plan.preserved, *plan.excluded], key=lambda item: item.path)
    payload = {"schema": "agent-runtime-sync-reconcile/v1", "root": str(plan.root), "project": plan.config.project,
        "profiles": list(plan.config.profiles), "capabilities": list(plan.config.capabilities),
        "upstream": {"package": plan.config.upstream_package, "remote_url": plan.config.upstream_remote_url, "ref": plan.config.upstream_ref},
        "template_root": str(plan.template_root), "template_digest": _template_digest(plan.template_root), "lock_schema": plan.lock_schema,
        "actions": [{"path": a.path, "ownership": a.ownership, "action": a.action, "reason": a.reason, "safety": a.safety} for a in actions],
        "counts": {"safe_updates": len(plan.updates), "conflicts": len(plan.conflicts), "preserved": len(plan.preserved), "excluded": len(plan.excluded)}}
    return json.dumps(payload, indent=2, sort_keys=True)


def render_reconcile(plan: SyncPlan) -> str:
    lines = ["# Agent Runtime Sync Reconcile", f"project={plan.config.project}", f"template_root={plan.template_root}", f"safe_updates={len(plan.updates)}", f"conflicts={len(plan.conflicts)}", f"preserved={len(plan.preserved)}", f"excluded={len(plan.excluded)}"]
    lines.extend(f"- {a.path} {a.ownership} {a.action} {a.safety}: {a.reason}" for a in sorted([*plan.updates, *plan.conflicts, *plan.preserved, *plan.excluded], key=lambda item: item.path))
    return "\n".join(lines)


def _template_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in _template_files(root):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(_canonical_content(path))
    return f"sha256:{digest.hexdigest()}"


def _diff_update(update: TemplateUpdate) -> str:
    source_lines = _read(update.source).splitlines(keepends=True)
    if update.target.exists():
        target_lines = _read(update.target).splitlines(keepends=True)
        fromfile = f"host/{update.path}"
    else:
        target_lines = []
        fromfile = "/dev/null"
    return "".join(
        difflib.unified_diff(
            target_lines,
            source_lines,
            fromfile=fromfile,
            tofile=f"upstream/{update.path}",
        )
    ).rstrip()


def render_diff(plan: SyncPlan) -> str:
    all_items = [*plan.updates, *plan.conflicts]
    if not all_items:
        return "No template updates available."
    return "\n\n".join(_diff_update(update) for update in all_items)


def _print_output(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None)
    if encoding:
        text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    sys.stdout.write(text)
    sys.stdout.write("\n")


def apply_updates(plan: SyncPlan) -> int:
    if plan.conflicts:
        _print_output(render_check(plan))
        _print_output("applied=0")
        return 1
    applied = 0
    for update in plan.updates:
        update.target.parent.mkdir(parents=True, exist_ok=True)
        update.target.write_text(_read(update.source), encoding="utf-8")
        applied += 1
    if not plan.updates:
        _print_output("No template updates available.")
    else:
        _print_output(render_check(plan))
    _print_output(f"applied={applied}")
    return 0


def apply_safe_updates(plan: SyncPlan) -> int:
    applied = 0
    for update in plan.updates:
        update.target.parent.mkdir(parents=True, exist_ok=True)
        update.target.write_bytes(update.source.read_bytes())
        applied += 1
    _print_output(render_reconcile(plan))
    _print_output(f"applied={applied}")
    _print_output(f"remaining_conflicts={len(plan.conflicts)}")
    return 1 if plan.conflicts else 0


def run_sync(root: Path, mode: str, template_root: Path | None = None, json_output: bool = False) -> int:
    plan = build_sync_plan(root, template_root=template_root)
    if plan.config.allow_silent_overwrite:
        _print_output(render_check(plan))
        _print_output("ERROR: sync.allow_silent_overwrite must be false.")
        return 1

    if mode == "check":
        _print_output(render_check(plan))
        return 1 if plan.conflicts else 0
    elif mode == "diff":
        _print_output(render_diff(plan))
    elif mode == "apply":
        return apply_updates(plan)
    elif mode == "apply-safe":
        return apply_safe_updates(plan)
    elif mode == "reconcile":
        _print_output(reconcile_json(plan) if json_output else render_reconcile(plan))
        return 1 if plan.conflicts else 0
    else:
        raise ValueError(f"unknown sync mode: {mode}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check/diff/apply Agent Runtime template updates")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Host project root")
    parser.add_argument("--template-root", type=Path, default=None, help="Template root override")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report available updates without writing")
    mode.add_argument("--diff", action="store_true", help="Show exact template changes")
    mode.add_argument("--apply", action="store_true", help="Apply safe selected updates")
    mode.add_argument("--apply-safe", action="store_true")
    mode.add_argument("--reconcile", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.json and not args.reconcile:
        parser.error("--json is only valid with --reconcile")
    if args.check:
        mode = "check"
    elif args.diff:
        mode = "diff"
    elif args.apply:
        mode = "apply"
    elif args.apply_safe:
        mode = "apply-safe"
    else:
        mode = "reconcile"
    return run_sync(args.root, mode, template_root=args.template_root, json_output=args.json)
