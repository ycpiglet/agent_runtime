from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from . import claim_store as _claim_store
from .config import AgentRuntimeConfig, default_ownership, load_config
from .template_profiles import selected_paths

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
    claim_store_state: str = "pristine"
    claim_store_finding: str | None = None
    runtime_migrations: tuple[str, ...] = ()


def default_template_root() -> Path:
    return Path(__file__).resolve().parent / "templates" / "project"


def _is_runtime_artifact(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def _template_files(template_root: Path, profiles: tuple[str, ...] | None = None) -> list[Path]:
    if not template_root.exists():
        return []
    # Test and explicit override roots remain plain file fixtures; the packaged
    # root is fail-closed because it always carries the manifest.
    manifest = template_root / "agents/project/RUNTIME-PROFILE-MANIFEST.json"
    if profiles is not None and not manifest.exists() and template_root.resolve() == default_template_root().resolve():
        raise ValueError("packaged template profile manifest is missing")
    source = selected_paths(template_root, profiles) if profiles is not None and manifest.exists() else tuple(template_root.rglob("*"))
    return sorted(
        (path for path in source if path.is_file() and not _is_runtime_artifact(path)),
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


def template_digest(template_root: Path, profiles: tuple[str, ...] | None = None) -> tuple[str, int]:
    """Canonical packaged-template digest shared with lock serialization."""
    digest = hashlib.sha256()
    files = _template_files(template_root, profiles)
    for path in files:
        digest.update(path.relative_to(template_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_content(path))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}", len(files)


def _unsafe_target(root: Path, target: Path) -> str | None:
    current = target
    while current != root:
        if current.is_symlink():
            return "symlink target or ancestor"
        if current.exists() and current != target and not current.is_dir():
            return "non-directory ancestor"
        current = current.parent
    if target.exists() and not target.is_file():
        return "non-regular target"
    return None


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
    return default_ownership(path)


def build_sync_plan(root: Path, template_root: Path | None = None) -> SyncPlan:
    root = root.resolve()
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
    claim_store = _claim_store.inspect_store(root)
    runtime_migrations = (
        ("claim-store-adopt-existing",)
        if claim_store.state == "migration-required"
        else ()
    )
    for source in _template_files(resolved_template_root, config.profiles):
        rel = source.relative_to(resolved_template_root).as_posix()
        ownership = _ownership(config, rel)
        target = root / rel
        if ownership in {"host_owned", "generated"}:
            excluded.append(TemplateUpdate(rel, "excluded", source, target, ownership, "owner-controlled path", "never"))
            continue
        unsafe = _unsafe_target(root, target)
        if unsafe:
            conflicts.append(TemplateUpdate(rel, "conflict", source, target, ownership, unsafe, "unsafe"))
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
        conflicts.append(TemplateUpdate(rel, "conflict", source, target, ownership, "host content differs", "blocked"))
    return SyncPlan(
        root=root,
        config=config,
        template_root=resolved_template_root,
        updates=tuple(updates),
        conflicts=tuple(conflicts),
        preserved=tuple(preserved), excluded=tuple(excluded), lock_schema=str(lock.get("schema", "none")),
        prior_managed=tuple(sorted(managed_files)), seeded=tuple(sorted(seeded)),
        claim_store_state=claim_store.state,
        claim_store_finding=claim_store.finding,
        runtime_migrations=runtime_migrations,
    )


def render_check(plan: SyncPlan) -> str:
    status = (
        "blocked"
        if plan.config.allow_silent_overwrite
        or plan.claim_store_state == "integrity-invalid"
        else "ready"
    )
    lines = [
        "# Agent Runtime Sync Check",
        "",
        f"project={plan.config.project}",
        f"mode={plan.config.sync_mode}",
        f"allow_silent_overwrite={str(plan.config.allow_silent_overwrite).lower()}",
        f"status={status}",
        f"updates={len(plan.updates)}",
        f"conflicts={len(plan.conflicts)}",
        f"claim_store_state={plan.claim_store_state}",
        f"runtime_migrations={len(plan.runtime_migrations)}",
    ]
    if plan.claim_store_finding:
        lines.append(f"- claim-store {plan.claim_store_finding}")
    for migration in plan.runtime_migrations:
        lines.append(f"- migrate {migration}")
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
        "template_root": str(plan.template_root), "template_digest": template_digest(plan.template_root, plan.config.profiles)[0], "lock_schema": plan.lock_schema,
        "lock_migration": {"none": "new", "agent-runtime-lock/v1": "migrate-v1", "agent-runtime-lock/v2": "current"}.get(plan.lock_schema, "unknown"),
        "claim_store": {"state": plan.claim_store_state, "finding": plan.claim_store_finding},
        "runtime_migrations": list(plan.runtime_migrations),
        "actions": [{"path": a.path, "ownership": a.ownership, "action": a.action, "reason": a.reason, "safety": a.safety} for a in actions],
        "counts": {"safe_updates": len(plan.updates), "conflicts": len(plan.conflicts), "preserved": len(plan.preserved), "excluded": len(plan.excluded)}}
    return json.dumps(payload, indent=2, sort_keys=True)


def render_reconcile(plan: SyncPlan) -> str:
    lines = ["# Agent Runtime Sync Reconcile", f"project={plan.config.project}", f"template_root={plan.template_root}", f"safe_updates={len(plan.updates)}", f"conflicts={len(plan.conflicts)}", f"preserved={len(plan.preserved)}", f"excluded={len(plan.excluded)}", f"claim_store_state={plan.claim_store_state}", f"runtime_migrations={len(plan.runtime_migrations)}"]
    if plan.claim_store_finding:
        lines.append(f"- claim-store {plan.claim_store_finding}")
    lines.extend(f"- migrate {migration}" for migration in plan.runtime_migrations)
    lines.extend(f"- {a.path} {a.ownership} {a.action} {a.safety}: {a.reason}" for a in sorted([*plan.updates, *plan.conflicts, *plan.preserved, *plan.excluded], key=lambda item: item.path))
    return "\n".join(lines)


def _diff_update(update: TemplateUpdate) -> str:
    if update.safety == "unsafe":
        return f"# unsafe conflict {update.path}: {update.reason}"
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
    lines = [f"claim_store_state={plan.claim_store_state}"]
    if plan.claim_store_finding:
        lines.append(f"- claim-store {plan.claim_store_finding}")
    if not all_items:
        lines.append("No template updates available.")
        return "\n".join(lines)
    lines.append("")
    lines.append("\n\n".join(_diff_update(update) for update in all_items))
    return "\n".join(lines)


def _print_output(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None)
    if encoding:
        text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    sys.stdout.write(text)
    sys.stdout.write("\n")


@dataclass(frozen=True)
class _ObservedTarget:
    state: str
    content: bytes | None = None


@dataclass(frozen=True)
class _PreparedUpdate:
    update: TemplateUpdate
    expected: bytes
    before: _ObservedTarget


@dataclass(frozen=True)
class _TemplateApplication:
    state: str
    applied: int | None
    observed_applied: int


def _observe_target(path: Path) -> _ObservedTarget:
    try:
        if not path.exists():
            return _ObservedTarget("missing")
        if not path.is_file():
            return _ObservedTarget("non-regular")
        return _ObservedTarget("content", _canonical_content(path))
    except OSError:
        return _ObservedTarget("unknown")


def _prepare_updates(updates: tuple[TemplateUpdate, ...]) -> tuple[_PreparedUpdate, ...]:
    return tuple(
        _PreparedUpdate(
            update=update,
            expected=_canonical_content(update.source),
            before=_observe_target(update.target),
        )
        for update in updates
    )


def _observe_template_application(
    prepared: tuple[_PreparedUpdate, ...],
    *,
    required: bool,
) -> _TemplateApplication:
    if not prepared:
        state = "not-applied" if required else "not-required"
        return _TemplateApplication(state, 0, 0)

    committed = 0
    mutation_observed = False
    unknown = False
    for item in prepared:
        after = _observe_target(item.update.target)
        if after.state == "unknown":
            unknown = True
            continue
        if after.state == "content" and after.content == item.expected:
            committed += 1
            continue
        if item.before.state == "unknown":
            unknown = True
            continue
        if after != item.before:
            mutation_observed = True

    if unknown:
        return _TemplateApplication("unknown", None, committed)
    if committed == len(prepared):
        return _TemplateApplication("committed", committed, committed)
    if committed or mutation_observed:
        return _TemplateApplication("partial", committed, committed)
    return _TemplateApplication("not-applied", 0, 0)


def _observe_claim_store_migration(root: Path, *, required: bool) -> str:
    if not required:
        return "not-required"
    try:
        state = _claim_store.inspect_store(root).state
    except (_claim_store.ClaimStoreError, OSError, RuntimeError):
        return "unknown"
    if state == "initialized":
        return "applied"
    if state == "migration-required":
        return "not-applied"
    return "unknown"


def _post_apply_plan(
    root: Path,
    template_root: Path,
) -> tuple[SyncPlan | None, str | None]:
    try:
        return build_sync_plan(root, template_root=template_root), None
    except (
        _claim_store.ClaimStoreError,
        OSError,
        RuntimeError,
        UnicodeError,
        ValueError,
    ) as exc:
        return None, str(exc)


def _print_apply_observation(
    migration: str,
    templates: _TemplateApplication,
) -> None:
    _print_output(f"claim_store_migration={migration}")
    _print_output(f"template_application={templates.state}")
    if templates.applied is None:
        _print_output("applied=unknown")
        _print_output(f"observed_applied={templates.observed_applied}")
    else:
        _print_output(f"applied={templates.applied}")


def _apply_exit_failed(
    *,
    error: Exception | None,
    post: SyncPlan | None,
    migration: str,
    templates: _TemplateApplication,
) -> bool:
    if error is not None or post is None:
        return True
    if migration in {"not-applied", "unknown"}:
        return True
    if migration == "applied" and post.claim_store_state != "initialized":
        return True
    if templates.state not in {"committed", "not-required"}:
        return True
    return bool(
        post.updates
        or post.runtime_migrations
        or post.conflicts
        or post.claim_store_state == "integrity-invalid"
    )


def apply_updates(plan: SyncPlan) -> int:
    initial = build_sync_plan(plan.root, template_root=plan.template_root)
    if initial.conflicts or initial.claim_store_state == "integrity-invalid":
        _print_output(render_check(initial))
        _print_output("applied=0")
        return 1
    migration_required = initial.claim_store_state == "migration-required"
    template_updates_required = bool(initial.updates)
    prepared: tuple[_PreparedUpdate, ...] = ()
    error: Exception | None = None
    try:
        with _claim_store.store_lock(plan.root):
            fresh = build_sync_plan(plan.root, template_root=plan.template_root)
            migration_required = fresh.claim_store_state == "migration-required"
            template_updates_required = bool(fresh.updates)
            if fresh.conflicts or fresh.claim_store_state == "integrity-invalid":
                _print_output(render_check(fresh))
                _print_output("applied=0")
                return 1
            for update in fresh.updates:
                if _unsafe_target(fresh.root, update.target):
                    _print_output(render_check(fresh))
                    _print_output("applied=0")
                    return 1
            prepared = _prepare_updates(fresh.updates)
            if fresh.claim_store_state == "migration-required":
                _claim_store.adopt_legacy_store(fresh.root)
            for update in fresh.updates:
                update.target.parent.mkdir(parents=True, exist_ok=True)
                update.target.write_text(_read(update.source), encoding="utf-8")
    except (_claim_store.ClaimStoreError, TimeoutError, OSError) as exc:
        error = exc

    migration = _observe_claim_store_migration(
        plan.root,
        required=migration_required,
    )
    templates = _observe_template_application(
        prepared,
        required=template_updates_required,
    )
    post, post_error = _post_apply_plan(plan.root, plan.template_root)
    if error is not None:
        _print_output(f"ERROR: sync apply failed: {error}")
    if post is None:
        _print_output("post_apply_plan=unavailable")
        if post_error:
            _print_output(f"post_apply_error={post_error}")
    else:
        _print_output(render_check(post))
    if not prepared:
        _print_output("No template updates available.")
    _print_apply_observation(migration, templates)
    failed = _apply_exit_failed(
        error=error,
        post=post,
        migration=migration,
        templates=templates,
    )
    return 1 if failed else 0


def apply_safe_updates(plan: SyncPlan) -> int:
    initial = build_sync_plan(plan.root, template_root=plan.template_root)
    planned_conflicts = {item.path for item in plan.conflicts}
    if (
        initial.claim_store_state == "integrity-invalid"
        or any(item.path not in planned_conflicts for item in initial.conflicts)
    ):
        _print_output(render_reconcile(initial))
        _print_output("applied=0")
        _print_output(f"remaining_conflicts={len(initial.conflicts)}")
        return 1
    migration_required = initial.claim_store_state == "migration-required"
    template_updates_required = bool(initial.updates)
    prepared: tuple[_PreparedUpdate, ...] = ()
    error: Exception | None = None
    try:
        with _claim_store.store_lock(plan.root):
            fresh = build_sync_plan(plan.root, template_root=plan.template_root)
            migration_required = fresh.claim_store_state == "migration-required"
            template_updates_required = bool(fresh.updates)
            if (
                fresh.claim_store_state == "integrity-invalid"
                or any(item.path not in planned_conflicts for item in fresh.conflicts)
            ):
                _print_output(render_reconcile(fresh))
                _print_output("applied=0")
                _print_output(f"remaining_conflicts={len(fresh.conflicts)}")
                return 1
            safe_updates = tuple(
                update
                for update in fresh.updates
                if _unsafe_target(fresh.root, update.target) is None
            )
            prepared = _prepare_updates(safe_updates)
            if fresh.claim_store_state == "migration-required":
                _claim_store.adopt_legacy_store(fresh.root)
            for update in safe_updates:
                if _unsafe_target(fresh.root, update.target) is not None:
                    continue
                update.target.parent.mkdir(parents=True, exist_ok=True)
                update.target.write_bytes(update.source.read_bytes())
    except (_claim_store.ClaimStoreError, TimeoutError, OSError) as exc:
        error = exc

    migration = _observe_claim_store_migration(
        plan.root,
        required=migration_required,
    )
    templates = _observe_template_application(
        prepared,
        required=template_updates_required,
    )
    post, post_error = _post_apply_plan(plan.root, plan.template_root)
    if error is not None:
        _print_output(f"ERROR: sync apply-safe failed: {error}")
    if post is None:
        _print_output("post_apply_plan=unavailable")
        if post_error:
            _print_output(f"post_apply_error={post_error}")
    else:
        _print_output(render_reconcile(post))
    _print_apply_observation(migration, templates)
    if post is None:
        _print_output("remaining_conflicts=unknown")
    else:
        _print_output(f"remaining_conflicts={len(post.conflicts)}")
    failed = _apply_exit_failed(
        error=error,
        post=post,
        migration=migration,
        templates=templates,
    )
    return 1 if failed else 0


def run_sync(root: Path, mode: str, template_root: Path | None = None, json_output: bool = False) -> int:
    plan = build_sync_plan(root, template_root=template_root)
    if plan.config.allow_silent_overwrite:
        _print_output(render_check(plan))
        _print_output("ERROR: sync.allow_silent_overwrite must be false.")
        return 1

    if mode == "check":
        _print_output(render_check(plan))
        return 1 if plan.conflicts or plan.claim_store_state == "integrity-invalid" else 0
    elif mode == "diff":
        _print_output(render_diff(plan))
        return 1 if plan.claim_store_state == "integrity-invalid" else 0
    elif mode == "apply":
        return apply_updates(plan)
    elif mode == "apply-safe":
        return apply_safe_updates(plan)
    elif mode == "reconcile":
        _print_output(reconcile_json(plan) if json_output else render_reconcile(plan))
        return 1 if plan.conflicts or plan.claim_store_state == "integrity-invalid" else 0
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
