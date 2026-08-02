"""Create and release parallel-agent task claim records.

The dispatcher writes identity-rich claim records while keeping machine identity
separate from the human-facing display name:

- agent_role: durable role expectation, for policy/routing;
- agent_instance_id: unique execution unit;
- display_name: readable label for UI/status surfaces;
- callsite_id: terminal or launcher origin.

Release enforces the Owner rule "작업자 자기검증 금지 — 항상 다른 에이전트가 검증":
the independent (W4b) verifier identity passed via --verified-by must DIFFER from
the claim's worker agent_instance_id, and a verification evidence ref is required
by default (--allow-missing-evidence is a loud transitional escape). Claims that
were already released before this gate existed are exempt; only new release
invocations enforce it.

Create runs the deferred plan revalidation check (T2, TASK-AR-506) by default.
Claims bound to a canonical taskset or complete unit require a valid T0 entry
in agents/project/work-items/PLAN-ASSUMPTIONS.json, while legacy identity-only
claims retain their migration-compatible no-snapshot path. Drifted anchors
refuse claim creation until a replan review re-records them
(--skip-plan-check is a loud transitional escape for drift only). Direct,
taskset, and wave claim entry points share the same readiness-before-mutation
contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NamedTuple

import atomic_io
import backlog_board
import claim_guard
import compound_record
import model_routing
import plan_assumption_gate
import status_alias
import task_unit_readiness_gate
from agent_runtime import claim_store
from agent_instance_registry import record_claim_instance
from footprint_conflict_gate import ACTIVE_CLAIM_STATUSES as FOOTPRINT_ACTIVE_STATUSES
from footprint_conflict_gate import footprints_overlap
from pane_event_log import append_event

try:
    import a2a_claim_emitter
except ImportError:  # optional in the portable project template
    a2a_claim_emitter = None

try:
    import role_routing
except ImportError:  # optional in the portable project template
    role_routing = None


def _claim_autocommit_enabled(*, cli_opt_in: bool = False) -> bool:
    """Return whether this invocation explicitly authorizes an SCM commit.

    Claim files are normal Runtime persistence; changing a host's Git HEAD is
    a separate external effect.  Keep the crash-safety path available for
    trusted control repositories, but never infer that authority from an
    absent or malformed environment value.
    """

    if cli_opt_in:
        return True
    raw = os.environ.get("AGENT_RUNTIME_CLAIM_AUTOCOMMIT")
    if raw is None:
        return False
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized not in {"0", "false", "no", "off", ""}:
        print(
            "warning: invalid AGENT_RUNTIME_CLAIM_AUTOCOMMIT value; "
            "claim artifacts will remain uncommitted",
            file=sys.stderr,
        )
    return False


SCHEMA = "agent-runtime-task-claim/v1"
SCOPE_BINDING_SCHEMA = "agent-runtime-claim-scope-binding/v1"
SECURITY_SERVICE_GATE_SHA256 = (
    "a40384ca372d1c986538800687c8e339c45ed72bd3f167631be2f6e799ce32ce"
)
SECURITY_SERVICE_GATE_MAX_BYTES = 64 * 1024
SECURITY_SERVICE_PROFILE_STATE_MAX_BYTES = 128 * 1024
SECURITY_SERVICE_PROFILE_MARKERS = (
    ".allimbot.json",
    "agents/project/SECURITY-SERVICE-POLICY.json",
    "docs/security-service.md",
    "scripts/allimbot.py",
)
SECURITY_SERVICE_GATE_BOOTSTRAP = (
    "import sys\n"
    "_gate_path = sys.argv[1]\n"
    "sys.argv = sys.argv[1:]\n"
    "_source = sys.stdin.buffer.read()\n"
    "exec(compile(_source, _gate_path, 'exec'), "
    "{'__name__': '__main__', '__file__': _gate_path})\n"
)
ACTIVE_STATUSES = claim_store.ACTIVE_CLAIM_STATUSES
ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}
COMPLETION_PHASES = {"done", "complete", "completed", "released"}
PROGRESS_FIELDS = (
    "phase",
    "progress_pct",
    "step_index",
    "step_total",
    "status_text",
)


class _CreatePreparation(NamedTuple):
    """Read-only inputs resolved before claim-store lock creation."""

    task_set_id: str
    strict_claim_preflight: bool
    target_files: tuple[str, ...]
    escalation_triggers: tuple[str, ...]
    routing_decision: dict[str, Any]
    token_budgets: dict[str, int | None]
    defect_signatures: tuple[str, ...]
    knowledge_matches: tuple[dict[str, Any], ...]


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _scope_binding(
    *,
    task_id: object,
    unit_id: object,
    unit_spec: object,
    target_files: object,
    stop_condition: object,
    bound_at: str,
) -> dict[str, Any]:
    targets = (
        sorted({str(item) for item in target_files})
        if isinstance(target_files, (list, tuple, set))
        else []
    )
    components = {
        "task": _canonical_sha256({"task_id": str(task_id or "")}),
        "unit": _canonical_sha256(
            {
                "unit_id": str(unit_id or ""),
                "unit_spec": str(unit_spec or ""),
            }
        ),
        "target_files": _canonical_sha256(targets),
        "stop_condition": _canonical_sha256(str(stop_condition or "")),
    }
    return {
        "schema": SCOPE_BINDING_SCHEMA,
        "digest": _canonical_sha256(components),
        "components": components,
        "bound_at": bound_at,
    }


def _binding_for_claim(
    claim: dict[str, Any],
    *,
    bound_at: str,
    target_files: object | None = None,
    stop_condition: object | None = None,
) -> dict[str, Any]:
    return _scope_binding(
        task_id=claim.get("task_id"),
        unit_id=claim.get("unit_id"),
        unit_spec=claim.get("unit_spec"),
        target_files=(
            claim.get("target_files", [])
            if target_files is None
            else target_files
        ),
        stop_condition=(
            claim.get("stop_condition", "")
            if stop_condition is None
            else stop_condition
        ),
        bound_at=bound_at,
    )


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str, *, sep: str = "-") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", sep, value.strip().lower())
    text = re.sub(rf"{re.escape(sep)}+", sep, text)
    return text.strip(sep) or "item"


def _display_role(role: str) -> str:
    return _slug(role, sep="_")


def _role_initials(role: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", role.lower()) if part]
    if not parts:
        return "ag"
    if len(parts) == 1:
        return parts[0][:2].ljust(2, "x")
    return "".join(part[0] for part in parts)[:4]


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _tz_label(value: datetime) -> str:
    offset = value.utcoffset()
    if offset == timedelta(hours=9):
        return "kst"
    if offset == timedelta(0):
        return "utc"
    if offset is None:
        return "local"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "p" if total_minutes >= 0 else "m"
    total_minutes = abs(total_minutes)
    return f"utc{sign}{total_minutes // 60:02d}{total_minutes % 60:02d}"


def _claim_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


_CLAIM_ARTIFACT_PARENT = Path("agents") / "runtime" / "task_claims"
_WINDOWS_REPARSE_POINT = getattr(
    stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400
)


def _is_path_alias(metadata: os.stat_result) -> bool:
    attributes = int(getattr(metadata, "st_file_attributes", 0) or 0)
    reparse_tag = int(getattr(metadata, "st_reparse_tag", 0) or 0)
    return (
        stat.S_ISLNK(metadata.st_mode)
        or bool(attributes & _WINDOWS_REPARSE_POINT)
        or bool(reparse_tag)
    )


def _claim_artifact_ref_error(value: object, field: str) -> str | None:
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        return None
    path = Path(text)
    suffix = {"handoff_path": ".handoff.md", "log_path": ".log.md"}[field]
    if (
        path.is_absolute()
        or path.parent != _CLAIM_ARTIFACT_PARENT
        or not path.name.endswith(suffix)
        or path.name in {suffix, ".", ".."}
    ):
        return (
            f"{field} must be a direct {suffix} file under "
            "agents/runtime/task_claims"
        )
    return None


def _direct_repo_file_ref(root: Path, value: object, label: str) -> str:
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"{label} must be a repo-relative direct regular file")
    current = root
    for index, component in enumerate(path.parts):
        current = current / component
        try:
            metadata = current.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"{label} not found: {path.as_posix()}") from exc
        except OSError as exc:
            raise ValueError(f"{label} is unavailable: {path.as_posix()}") from exc
        if _is_path_alias(metadata):
            raise ValueError(f"{label} must not use a symlink or reparse point")
        if index < len(path.parts) - 1:
            if not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(f"{label} parent is not a direct directory")
        elif not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"{label} must be a direct regular file")
    return path.as_posix()


def _claim_artifact_file_ref(root: Path, value: object, field: str) -> str:
    finding = _claim_artifact_ref_error(value, field)
    if finding:
        raise ValueError(finding)
    return _direct_repo_file_ref(root, value, field)


def _entry_exists(path: Path, label: str) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    return True


def _missing_directories(path: Path, root: Path) -> list[Path]:
    """Return absent ancestors, child first, without crossing the repo root."""

    missing: list[Path] = []
    current = path
    while current != root:
        if _entry_exists(current, "claim artifact directory"):
            break
        missing.append(current)
        current = current.parent
    return missing


class _CreatedPublication(NamedTuple):
    path: Path
    expected: bytes
    device: int
    inode: int


def _created_publication(
    path: Path,
    expected: bytes,
    identity: atomic_io.PublishedFileIdentity,
) -> _CreatedPublication:
    """Register rollback authority without re-opening a committed path."""

    return _CreatedPublication(
        path=path,
        expected=expected,
        device=identity.device,
        inode=identity.inode,
    )


def _remove_owned_publication(
    path: Path,
    *,
    expected: bytes,
    identity: tuple[int, int] | None = None,
) -> str | None:
    """Remove a transaction-owned direct file, refusing ambiguous cleanup."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        return f"rollback could not inspect {path}"
    if _is_path_alias(metadata) or not stat.S_ISREG(metadata.st_mode):
        return f"rollback refused non-regular publication {path}"
    if metadata.st_size != len(expected):
        return f"rollback refused resized publication {path}"
    if identity is not None and (
        int(metadata.st_dev),
        int(metadata.st_ino),
    ) != identity:
        return f"rollback refused replaced publication {path}"
    try:
        payload = path.read_bytes()
    except OSError:
        return f"rollback could not read publication {path}"
    if payload != expected:
        return f"rollback refused changed publication {path}"
    try:
        path.unlink()
    except OSError:
        return f"rollback could not remove publication {path}"
    return None


def _transaction_marker_payload(
    path: Path,
    *,
    claim_id: str,
) -> tuple[bytes | None, str | None]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, f"rollback could not inspect marker {path}"
    if (
        _is_path_alias(metadata)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_size > claim_store.MARKER_MAX_BYTES
    ):
        return None, f"rollback refused noncanonical marker {path}"
    try:
        payload = path.read_bytes()
        parsed = json.loads(payload.decode("utf-8"))
        generation = uuid.UUID(str(parsed.get("generation_id")))
    except (
        AttributeError,
        UnicodeError,
        json.JSONDecodeError,
        OSError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return None, f"rollback refused malformed marker {path}"
    if (
        not isinstance(parsed, dict)
        or set(parsed) != {"schema", "generation_id", "witness_claim_id"}
        or parsed.get("schema") != claim_store.MARKER_SCHEMA
        or parsed.get("witness_claim_id") != claim_id
        or generation.version != 4
        or str(generation) != parsed.get("generation_id")
    ):
        return None, f"rollback refused unrelated marker {path}"
    return payload, None


def _marker_absence_finding(path: Path) -> str | None:
    """Prove a transaction marker is absent before deleting its witness."""

    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except (OSError, RuntimeError):
        return f"rollback could not prove marker absence {path}"
    return f"rollback left marker publication {path}"


def _rollback_claim_creation(
    root: Path,
    *,
    claim_id: str,
    publications: tuple[_CreatedPublication, ...],
    pristine_store: bool,
    missing_directories: tuple[Path, ...],
) -> list[str]:
    findings: list[str] = []
    preserve_witness = False
    if pristine_store:
        outer = claim_store.outer_marker_path(root)
        inner = _claim_dir(root) / ".claim-store"
        outer_payload, outer_finding = _transaction_marker_payload(
            outer,
            claim_id=claim_id,
        )
        inner_payload, inner_finding = _transaction_marker_payload(
            inner,
            claim_id=claim_id,
        )
        findings.extend(
            finding
            for finding in (outer_finding, inner_finding)
            if finding is not None
        )
        if not findings and inner_payload is not None:
            if (
                outer_payload is not None
                and outer_payload != inner_payload
                and not inner_payload.startswith(outer_payload)
            ):
                findings.append("rollback refused mismatched marker pair")
            else:
                if outer_payload is not None:
                    finding = _remove_owned_publication(
                        outer,
                        expected=outer_payload,
                    )
                    if finding:
                        findings.append(finding)
                finding = _remove_owned_publication(
                    inner,
                    expected=inner_payload,
                )
                if finding:
                    findings.append(finding)
        elif not findings and outer_payload is not None:
            findings.append("rollback refused outer-only marker")
        findings.extend(
            finding
            for finding in (
                _marker_absence_finding(outer),
                _marker_absence_finding(inner),
            )
            if finding is not None
        )
        preserve_witness = bool(findings)
        if preserve_witness:
            findings.insert(
                0,
                "claim-store recovery-required: marker rollback is incomplete; "
                "witness claim and artifacts were preserved"
            )
    if not preserve_witness:
        for publication in reversed(publications):
            finding = _remove_owned_publication(
                publication.path,
                expected=publication.expected,
                identity=(publication.device, publication.inode),
            )
            if finding:
                findings.append(finding)
    for directory in missing_directories:
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            # Never remove an ancestor that another actor populated meanwhile.
            continue
    return findings


def _claim_files(root: Path) -> list[Path]:
    base = _claim_dir(root)
    if not base.is_dir():
        return []
    return sorted(base.glob("*.json"), key=lambda path: path.name.lower())


def _read_claim(path: Path) -> dict[str, Any]:
    return dict(claim_store.read_claim_payload(path))


def _read_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in _claim_files(root):
        records.append((path, _read_claim(path)))
    return records


def _is_active(payload: dict[str, Any]) -> bool:
    return str(payload.get("status") or "").strip().lower() in ACTIVE_STATUSES


def _active_task_claim_path(
    records: list[tuple[Path, dict[str, Any]]], task_id: str
) -> Path | None:
    for path, payload in records:
        if _is_active(payload) and str(payload.get("task_id") or "") == task_id:
            return path
    return None


def _is_explicit_overlay(payload: dict[str, Any]) -> bool:
    return payload.get("overlay") is True


def _resolved_worktree(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _has_git_worktree_marker(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _git_worktree_context(path: Path) -> tuple[Path, Path, bool] | None:
    """Return ``(top_level, common_dir, is_primary)`` for a registered worktree.

    A linked worktree has a ``.git`` *file*, while the primary checkout has a
    ``.git`` directory.  That distinction alone is not sufficient: a copied
    marker, a different repository, or an unregistered directory can look
    plausible.  Ask Git for both its common directory and registered worktree
    list, and fail closed when either identity cannot be established.

    ``None`` deliberately preserves the legacy marker-only behavior for the
    lightweight non-Git fixture hosts used by downstream adopters.  Callers
    that have already established a Git runtime root must reject ``None`` for
    the claimed worktree.
    """
    try:
        identity = subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "rev-parse",
                "--path-format=absolute",
                "--show-toplevel",
                "--git-common-dir",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if identity.returncode != 0:
        return None
    values = [line.strip() for line in identity.stdout.splitlines() if line.strip()]
    if len(values) != 2:
        return None
    top_level = Path(values[0]).resolve()
    common_dir = Path(values[1]).resolve()
    try:
        listing = subprocess.run(
            ["git", "-C", str(top_level), "worktree", "list", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if listing.returncode != 0:
        return None
    registered = [
        Path(line[9:]).resolve()
        for line in listing.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    if registered.count(top_level) != 1:
        return None
    primary = [
        candidate
        for candidate in registered
        if (candidate / ".git").is_dir()
        and (candidate / ".git").resolve() == common_dir
    ]
    if len(primary) != 1:
        return None
    return top_level, common_dir, top_level == primary[0]


def _is_git_repository(path: Path) -> bool:
    """Whether Git recognizes ``path`` as being inside any repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _is_orchestrator_claim(payload: dict[str, Any]) -> bool:
    role = str(payload.get("agent_role") or "").strip().lower()
    if role in ORCHESTRATOR_ROLES:
        return True
    mode = str(payload.get("mode") or "").strip().lower()
    scope = str(payload.get("worker_scope") or "").strip().lower()
    return mode == "orchestrator" or scope == "orchestrator"


def _claim_creation_errors(
    root: Path,
    claim: dict[str, Any],
    records: list[tuple[Path, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    if not _is_orchestrator_claim(claim):
        worktree_value = str(claim.get("worktree_path") or "").strip()
        if not worktree_value:
            errors.append("task worktree is not ready: missing worktree_path")
        else:
            worktree = _resolved_worktree(root, worktree_value)
            if not worktree.is_dir():
                errors.append(
                    f"task worktree is not ready: {worktree_value} does not exist; "
                    f"run: git worktree add -b {claim.get('branch')} {worktree_value}"
                )
            elif not _has_git_worktree_marker(worktree):
                errors.append(f"task worktree is not ready: {worktree_value} is not a git worktree")
            else:
                root_context = _git_worktree_context(root)
                worktree_context = _git_worktree_context(worktree)
                if root_context is not None:
                    if worktree_context is None:
                        errors.append(
                            f"task worktree is not ready: {worktree_value} is not a registered git worktree"
                        )
                    elif root_context[1] != worktree_context[1]:
                        errors.append(
                            f"task worktree is not ready: {worktree_value} belongs to a different git repository"
                        )
                    elif root_context[2]:
                        errors.append(
                            "task worktree is not ready: runtime root must be a registered linked "
                            "worktree, not the primary checkout"
                        )
                    elif worktree_context[2]:
                        errors.append(
                            "task worktree is not ready: worker claims must not point at the primary checkout"
                        )
                    elif worktree.resolve() != root.resolve():
                        errors.append(
                            "task worktree is not ready: worker claims must target the invoking "
                            "linked worktree itself"
                        )
                elif _is_git_repository(root):
                    errors.append(
                        "task worktree is not ready: runtime root is not an unambiguous registered git worktree"
                    )
                elif worktree == root.resolve():
                    # Preserve the old fail-closed behavior for non-Git
                    # fixture hosts, where a marker alone cannot prove a
                    # linked-worktree identity.
                    errors.append("task worktree is not ready: worker claims must not point at the main checkout")

    task_set_id = str(claim.get("task_set_id") or "").strip()
    allow_parallel = str(claim.get("allow_parallel_task_set") or "").strip().lower() == "true"
    if task_set_id and not allow_parallel:
        for path, payload in records:
            if not _is_active(payload):
                continue
            if str(payload.get("task_set_id") or "").strip() == task_set_id:
                errors.append(f"task set already has an active claim: {task_set_id} ({_rel(root, path)})")
                break
    return errors


def _unit_spec_target_files(root: Path, unit_spec: str) -> list[str]:
    spec_value = str(unit_spec or "").strip()
    if not spec_value:
        return []
    spec_path = Path(spec_value)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    if not spec_path.is_file():
        return []
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []
    meta, _ = backlog_board.parse_frontmatter(text)
    value = meta.get("target_files")
    if isinstance(value, list):
        return _normalize_target_files(value)
    if isinstance(value, str) and value.strip():
        return _normalize_target_files([value])
    return []


def _unit_spec_stop_condition(root: Path, unit_spec: str) -> str:
    spec_value = str(unit_spec or "").strip()
    if not spec_value:
        return ""
    spec_path = Path(spec_value)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    if not spec_path.is_file():
        return ""
    try:
        meta, _ = backlog_board.parse_frontmatter(
            spec_path.read_text(encoding="utf-8")
        )
    except OSError:
        return ""
    value = meta.get("stop_condition")
    return str(value).strip() if isinstance(value, str) else ""


def _normalize_target_files(values: list[object] | tuple[object, ...]) -> list[str]:
    """Turn readiness-only ``new:`` markers into real claim footprint paths."""

    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text.startswith("new:"):
            text = text.removeprefix("new:").strip()
        if text:
            normalized.append(text.replace("\\", "/"))
    return list(dict.fromkeys(normalized))


def _frontmatter_list(path: Path, field: str) -> list[str]:
    if not path.is_file():
        return []
    try:
        meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    value = meta.get(field)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _work_defect_signatures(root: Path, args: argparse.Namespace) -> list[str]:
    values = [str(value).strip() for value in (args.defect_signature or []) if str(value).strip()]
    task_path = root / "agents" / "lead_engineer" / "tasks" / f"{args.task_id}.md"
    values.extend(_frontmatter_list(task_path, "defect_signatures"))
    unit_spec = Path(str(args.unit_spec or ""))
    if not unit_spec.is_absolute():
        unit_spec = root / unit_spec
    values.extend(_frontmatter_list(unit_spec, "defect_signatures"))
    return list(dict.fromkeys(values))


def _knowledge_lookup(
    root: Path, args: argparse.Namespace
) -> tuple[list[str], list[dict[str, Any]]]:
    raw_signatures = _work_defect_signatures(root, args)
    signatures = compound_record.normalize_signatures(raw_signatures)
    work_ids = [value for value in (args.task_id, args.unit_id) if value]
    rows = compound_record.search_knowledge(
        root,
        work_ids=work_ids,
        defect_signatures=raw_signatures,
        include_legacy=True,
        limit=8,
    )
    bounded = [
        {
            key: row[key]
            for key in (
                "id",
                "path",
                "title",
                "score",
                "legacy",
                "work_ids",
                "defect_signatures",
            )
            if key in row
        }
        for row in rows
    ]
    return signatures, bounded


def _unit_spec_escalation_triggers(root: Path, unit_spec: str) -> list[str]:
    """Read a unit definition's frontmatter ``escalation_triggers``.

    Mirrors :func:`_unit_spec_target_files`: resolves ``unit_spec`` relative to
    ``root``, parses the frontmatter, and normalizes ``escalation_triggers`` to
    a list of non-empty stripped strings (accepting either a YAML list or a
    comma-separated string). Tolerant of a missing file/field/parse error -> [].
    """
    spec_value = str(unit_spec or "").strip()
    if not spec_value:
        return []
    spec_path = Path(spec_value)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    if not spec_path.is_file():
        return []
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []
    meta, _ = backlog_board.parse_frontmatter(text)
    value = meta.get("escalation_triggers")
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _work_item_meta(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    return dict(meta)


def _task_meta(root: Path, task_id: str) -> dict[str, Any]:
    return _work_item_meta(
        root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    )


def _unit_meta(root: Path, unit_spec: str) -> dict[str, Any]:
    value = str(unit_spec or "").strip()
    if not value:
        return {}
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return _work_item_meta(path)


def _resolve_target_files(root: Path, args: argparse.Namespace) -> list[str]:
    explicit = _normalize_target_files(tuple(args.target_file or ()))
    registered = _unit_spec_target_files(root, args.unit_spec)
    return list(dict.fromkeys((*explicit, *registered)))


def _resolve_escalation_triggers(root: Path, args: argparse.Namespace) -> list[str]:
    """Union of explicit ``--escalation-trigger`` args and the unit's inherited
    frontmatter triggers, deduped while preserving order (explicit-first).

    Explicit-first means an operator override is preserved ahead of inherited
    signals. The unit's triggers are stored verbatim (no pre-filter): the
    release seam intersects them with ``HIGH_RISK_TRIGGERS`` downstream.
    """
    explicit = [str(t).strip() for t in (args.escalation_trigger or ()) if str(t).strip()]
    task_inherited = _frontmatter_list(
        root / "agents" / "lead_engineer" / "tasks" / f"{args.task_id}.md",
        "escalation_triggers",
    )
    unit_inherited = _unit_spec_escalation_triggers(root, args.unit_spec)
    return list(dict.fromkeys(explicit + task_inherited + unit_inherited))


def _resolve_claim_routing(
    root: Path,
    args: argparse.Namespace,
    escalation_triggers: list[str],
) -> dict[str, Any]:
    task_meta = _task_meta(root, args.task_id)
    unit_meta = _unit_meta(root, args.unit_spec)
    if args.model_tier:
        unit_meta["model_tier"] = args.model_tier
    unit_meta["escalation_triggers"] = list(escalation_triggers)
    decision = model_routing.resolve_work_item_tier(task_meta, unit_meta)
    decision["routing_status"] = (
        "unverified"
        if decision["unknown_triggers"]
        else "escalated"
        if decision["selected_tier"] != decision["requested_tier"]
        else "selected"
    )
    return decision


def _resolve_token_budgets(
    root: Path,
    args: argparse.Namespace,
) -> dict[str, int | None]:
    """Resolve explicit -> unit -> task durable token budgets."""
    task_meta = _task_meta(root, args.task_id)
    unit_meta = _unit_meta(root, args.unit_spec)

    def _one(key: str) -> int | None:
        raw = (
            getattr(args, key, None)
            if getattr(args, key, None) not in (None, "")
            else unit_meta.get(key)
            if unit_meta.get(key) not in (None, "")
            else task_meta.get(key)
        )
        if raw in (None, ""):
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a non-negative integer") from exc
        if value < 0:
            raise ValueError(f"{key} must be a non-negative integer")
        return value

    return {
        "task_token_budget": _one("task_token_budget"),
        "claim_token_budget": _one("claim_token_budget"),
    }


def _is_footprint_active(payload: dict[str, Any]) -> bool:
    return str(payload.get("status") or "").strip().lower() in FOOTPRINT_ACTIVE_STATUSES


def _footprint_conflict_errors(
    root: Path,
    claim: dict[str, Any],
    records: list[tuple[Path, dict[str, Any]]],
) -> tuple[list[str], list[str]]:
    """Check the new claim's declared footprint against all active claims.

    Returns (errors, warnings). A footprint-less claim (legacy or new)
    conflicts with nothing but is reported as a one-line warning.
    """
    errors: list[str] = []
    warnings: list[str] = []
    target_files = [str(item) for item in (claim.get("target_files") or [])]
    if not target_files:
        warnings.append(
            f"warning: claim {claim.get('claim_id')} is footprint-less (no target_files); "
            "footprint conflict check skipped"
        )
        return errors, warnings
    conflicts: dict[str, list[tuple[str, str]]] = {}
    for path, payload in records:
        if not _is_footprint_active(payload):
            continue
        if str(payload.get("task_id") or "") == str(claim.get("task_id") or ""):
            continue
        other_id = str(payload.get("claim_id") or _rel(root, path))
        other_files = [str(item) for item in (payload.get("target_files") or [])]
        if not other_files:
            warnings.append(
                f"warning: active claim {other_id} is footprint-less (no target_files); "
                "it cannot block on footprint"
            )
            continue
        pairs = footprints_overlap(target_files, other_files)
        if pairs:
            conflicts.setdefault(other_id, []).extend(pairs)
    if conflicts:
        errors.append("footprint conflict with active claims: " + ", ".join(sorted(conflicts)))
        for other_id in sorted(conflicts):
            for a, b in conflicts[other_id]:
                errors.append(f"  overlap: {a} <-> {other_id}:{b}")
    return errors, warnings


def _next_slot(records: list[tuple[Path, dict[str, Any]]], *, role: str, mode: str) -> int:
    display_prefix = f"{_display_role(role)}@{_slug(mode)}-"
    used: set[int] = set()
    for _, payload in records:
        if not _is_active(payload):
            continue
        if str(payload.get("agent_role") or "") != role:
            continue
        display_name = str(payload.get("display_name") or "")
        if not display_name.startswith(display_prefix):
            continue
        suffix = display_name[len(display_prefix) :]
        if suffix.isdigit():
            used.add(int(suffix))
    slot = 1
    while slot in used:
        slot += 1
    return slot


def _ensure_text_file(path: Path, text: str) -> atomic_io.PublishedFileIdentity:
    if _entry_exists(path, "claim artifact"):
        raise FileExistsError(f"claim artifact already exists: {path}")
    return atomic_io.publish_text_owned_atomic(path, text)


def _build_claim(
    args: argparse.Namespace,
    records: list[tuple[Path, dict[str, Any]]],
    *,
    now: datetime,
    expires_at: datetime,
    target_files: list[str],
    escalation_triggers: list[str],
    routing_decision: dict[str, Any],
    token_budgets: dict[str, int | None],
    defect_signatures: list[str],
    knowledge_matches: list[dict[str, Any]],
) -> dict[str, Any]:
    suffix = _slug(args.suffix or uuid.uuid4().hex[:4])
    task_slug = _slug(args.task_id)
    mode = _slug(args.mode or "work")
    slot = _next_slot(records, role=args.agent_role, mode=mode)
    slot_text = f"{slot:02d}"
    display_name = args.display_name or f"{_display_role(args.agent_role)}@{mode}-{slot_text}"
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    agent_instance_id = args.agent_instance_id or (
        f"{_role_initials(args.agent_role)}-{timestamp}-{_tz_label(now)}-{suffix}"
    )
    claim_id = args.claim_id or f"CLAIM-{timestamp}-{task_slug}-{suffix}"
    worktree_path = args.worktree_path or f".worktrees/{args.task_id}"
    branch = args.branch or f"codex/{task_slug}-{mode}-{slot_text}"
    callsite_id = args.callsite_id or f"terminal:wt-{task_slug}:tab-{slot_text}"
    handoff_path = args.handoff_path or f"agents/runtime/task_claims/{claim_id}.handoff.md"
    log_path = args.log_path or f"agents/runtime/task_claims/{claim_id}.log.md"
    claimed_at = now.isoformat(timespec="seconds")
    expires_text = expires_at.isoformat(timespec="seconds")

    return {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "task_id": args.task_id,
        "agent_role": args.agent_role,
        "team_id": args.team_id,
        "agent_instance_id": agent_instance_id,
        "display_name": display_name,
        "callsite_id": callsite_id,
        "pane_id": args.pane_id or callsite_id,
        "mode": mode,
        "status": "claimed",
        "task_set_id": args.task_set_id,
        "active_scope": args.active_scope or args.task_set_id,
        "scope_transition_approved": bool(args.scope_transition_approved),
        "project_id": args.project_id,
        "unit_id": args.unit_id,
        "unit_spec": args.unit_spec,
        "requested_model_tier": routing_decision["requested_tier"],
        "selected_model_tier": routing_decision["selected_tier"],
        "model_tier": routing_decision["selected_tier"],
        "provider_tier": routing_decision["provider_tier"],
        "routing_status": routing_decision["routing_status"],
        "routing_reason": routing_decision["reason"],
        "routing_policy_id": routing_decision["routing_policy_id"],
        "routing_policy_reason": routing_decision["routing_policy_reason"],
        "routing_high_tier_authorized": routing_decision[
            "high_tier_authorized"
        ],
        "routing_escalation_reason": routing_decision[
            "registered_escalation_reason"
        ],
        "routing_registered_triggers": list(
            routing_decision["registered_escalation_triggers"]
        ),
        "routing_signals": list(routing_decision["escalation_triggers"]),
        "routing_unknown_triggers": list(routing_decision["unknown_triggers"]),
        "task_token_budget": token_budgets["task_token_budget"],
        "claim_token_budget": token_budgets["claim_token_budget"],
        "actual_model": None,
        "actual_model_status": "unverified",
        "wip_slot": args.wip_slot,
        "stop_condition": args.stop_condition,
        "phase": args.phase,
        "progress_pct": args.progress_pct,
        "step_index": args.step_index,
        "step_total": args.step_total,
        "status_text": args.status_text or f"Claim created for {args.task_id}",
        "worktree_path": worktree_path,
        "branch": branch,
        "claimed_at": claimed_at,
        "last_heartbeat": claimed_at,
        "updated_at": claimed_at,
        "expires_at": expires_text,
        "lease": {
            "claimed_at": claimed_at,
            "heartbeat_at": claimed_at,
            "expires_at": expires_text,
        },
        "handoff_path": handoff_path,
        "log_path": log_path,
        "allow_parallel_task_set": bool(args.allow_parallel_task_set),
        "tags": list(args.tag or ()),
        "escalation_triggers": list(escalation_triggers),
        "defect_signatures": list(defect_signatures),
        "knowledge_lookup": {
            "status": "matched" if knowledge_matches else "clear",
            "match_count": len(knowledge_matches),
        },
        "knowledge_matches": knowledge_matches,
        "target_files": list(target_files),
    }


def _claim_lease_window(args: argparse.Namespace) -> tuple[datetime, datetime]:
    """Validate the requested lease before claim-store authority is touched."""

    now = _parse_now(args.now)
    expires_at = claim_store.expiration_after(
        now,
        args.lease_minutes,
        unit="minutes",
        field="lease_minutes",
        minimum=1,
    )
    return now, expires_at


def _validate_create_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.claim_id and not claim_store.valid_claim_id(args.claim_id):
        errors.append("claim_id must use the canonical CLAIM-* identifier syntax")
    for field in ("handoff_path", "log_path"):
        finding = _claim_artifact_ref_error(getattr(args, field, None), field)
        if finding:
            errors.append(finding)
    if args.progress_pct < 0 or args.progress_pct > 100:
        errors.append("progress_pct must be between 0 and 100")
    if args.step_total < 1:
        errors.append("step_total must be at least 1")
    if args.step_index < 1 or args.step_index > args.step_total:
        errors.append("step_index must be between 1 and step_total")
    phase = str(args.phase or "").strip().lower()
    if phase in {"done", "complete", "completed", "released"} and args.step_index < args.step_total:
        errors.append("completion phase requires step_index to equal step_total")
    if not str(args.status_text or "").strip():
        errors.append("status_text is required")
    return errors


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = payload.get("status")
    path = payload.get("path")
    claim = payload.get("claim") or {}
    print(f"task-claim-dispatcher: {status}")
    if path:
        print(f"path={path}")
    if isinstance(claim, dict):
        print(f"claim_id={claim.get('claim_id')}")
        print(f"display_name={claim.get('display_name')}")


def _structured_claim_preflight_expected(root: Path, task_id: str) -> bool:
    """Return whether the host has adopted canonical task or unit records.

    Legacy lightweight callers can still create identity-only claims without
    first materializing the full work graph. Once the selected task is bound
    to a canonical taskset or a complete unit record, however, a direct claim
    must honor the same T0 and readiness gates used by taskset and wave
    dispatch.
    """

    tasks = backlog_board.load_tasks(
        root / "agents" / "lead_engineer" / "tasks"
    )
    for task in tasks:
        if task.task_id != task_id:
            continue
        task_set_id = str(task.task_set_id or "").strip()
        if (
            task_set_id
            and task_set_id != "TASKSET-AR-UNCLASSIFIED"
            and _canonical_taskset_statuses(root, task_set_id)
        ):
            return True

    for _path, meta, _body in task_unit_readiness_gate.load_unit_specs(root):
        if str(meta.get("task_id") or "").strip() != task_id:
            continue
        if (
            str(meta.get("unit_id") or "").strip()
            and str(meta.get("task_set_id") or "").strip()
            and str(meta.get("status") or "").strip()
        ):
            return True
    return False


def _plan_assumption_findings(
    root: Path, task_set_id: str
) -> list[str] | None:
    """Return legacy-compatible T2 findings for orchestration callers.

    ``None`` means no snapshot is recorded. Taskset and wave dispatchers retain
    that migration boundary; direct claims that have adopted structured work
    use ``_strict_plan_assumption_findings`` instead.
    """

    registry = plan_assumption_gate._load_registry(root)  # noqa: SLF001
    entry = next(
        (
            item
            for item in registry.get("assumption_sets", [])
            if isinstance(item, dict) and item.get("taskset_id") == task_set_id
        ),
        None,
    )
    if entry is None:
        return None
    findings: list[str] = []
    for anchor in entry.get("anchors", []):
        finding = plan_assumption_gate._check_anchor(root, anchor)  # noqa: SLF001
        if finding is not None:
            findings.append(finding)
    return findings


def _strict_plan_assumption_findings(root: Path, task_set_id: str) -> list[str]:
    """Return typed T0 registry and T2 drift findings for one taskset."""
    registry = plan_assumption_gate._load_registry(root)  # noqa: SLF001
    if not isinstance(registry, dict):
        return ["registry:invalid-root"]
    if registry.get("schema") != plan_assumption_gate.SCHEMA:
        return [f"registry:invalid-schema:{registry.get('schema') or 'missing'}"]
    sets = registry.get("assumption_sets")
    if not isinstance(sets, list):
        return ["registry:invalid-assumption-sets"]
    matches = [
        item
        for item in sets
        if isinstance(item, dict)
        and str(item.get("taskset_id") or "").strip() == task_set_id
    ]
    if not matches:
        return [f"registry:missing-taskset:{task_set_id}"]
    if len(matches) > 1:
        return [f"registry:duplicate-taskset:{task_set_id}"]
    entry = matches[0]
    anchors = entry.get("anchors")
    if not isinstance(anchors, list):
        return [f"registry:invalid-anchors:{task_set_id}"]
    if not anchors:
        return [f"registry:empty-anchors:{task_set_id}"]

    findings: list[str] = []
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            findings.append(f"registry:invalid-anchor:{task_set_id}:{index}")
            continue
        raw_path = anchor.get("path")
        raw_kind = anchor.get("kind")
        path = raw_path.strip() if isinstance(raw_path, str) else ""
        kind = raw_kind.strip() if isinstance(raw_kind, str) else ""
        path_value = Path(path) if path else None
        invalid_path = (
            path_value is None
            or path_value.is_absolute()
            or ".." in path_value.parts
        )
        digest = anchor.get("value")
        invalid_digest = (
            kind == "sha256"
            and (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            )
        )
        if invalid_path or kind not in {"sha256", "absent"} or invalid_digest:
            findings.append(f"registry:invalid-anchor:{task_set_id}:{index}")
            continue
        finding = plan_assumption_gate._check_anchor(root, anchor)  # noqa: SLF001
        if finding is not None:
            findings.append(f"{task_set_id}: {finding}")
    return findings


def _plan_check_refusal(
    root: Path,
    task_set_id: str,
    *,
    skip_plan_check: bool,
    require_snapshot: bool = False,
    emit_success: bool = True,
) -> bool:
    """T2 dispatch gate: verify the taskset's recorded plan assumptions.

    Returns True when claim creation must be refused. All output goes to
    stderr so --json stdout stays machine-readable.
    """
    try:
        findings = (
            _strict_plan_assumption_findings(root, task_set_id)
            if require_snapshot
            else _plan_assumption_findings(root, task_set_id)
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        findings = [f"registry-unreadable:{plan_assumption_gate.REGISTRY_REL}:{exc}"]
    if findings is None:
        if emit_success:
            print(
                f"note: no plan-assumption snapshot recorded for {task_set_id} "
                "(T0 skipped at registration); T2 drift check has nothing to verify. "
                "Record one with: python scripts/plan_assumption_gate.py record "
                f"--taskset {task_set_id} --design-record <review> --anchor <path>",
                file=sys.stderr,
            )
        return False
    if not findings:
        if emit_success:
            print(f"plan-assumption-gate: pass ({task_set_id})", file=sys.stderr)
        return False
    hard_registry_findings = [
        finding
        for finding in findings
        if finding.startswith(("registry:", "registry-unreadable:"))
    ]
    if skip_plan_check and not hard_registry_findings:
        if emit_success:
            print(
                "WARNING: --skip-plan-check used: creating claim for "
                f"{task_set_id} DESPITE drifted plan assumptions "
                "(T2 dispatch gate bypassed):",
                file=sys.stderr,
            )
            for finding in findings:
                print(f"  - {finding}", file=sys.stderr)
            print(
                "This is a transitional escape; run a replan review and re-record "
                "anchors as soon as possible.",
                file=sys.stderr,
            )
        return False
    if hard_registry_findings:
        print(
            f"claim preflight refused for {task_set_id}: missing or malformed "
            "plan assumptions (T0/T2 dispatch gate)",
            file=sys.stderr,
        )
    else:
        print(
            f"plan assumption drift detected for {task_set_id}: "
            "claim creation refused (T2 dispatch gate)",
            file=sys.stderr,
        )
    for finding in findings:
        print(f"claim-preflight:t0:{finding}", file=sys.stderr)
    print(
        "action=drifted plan assumptions; run a replan review for the affected "
        "taskset, then re-record anchors (python scripts/plan_assumption_gate.py "
        f"record --taskset {task_set_id} --design-record <review> --anchor <path>) "
        "before dispatch. --skip-plan-check is a loud transitional escape only.",
        file=sys.stderr,
    )
    return True


def _canonical_taskset_statuses(root: Path, task_set_id: str) -> list[str]:
    tasksets_dir = root / "agents" / "project" / "initiatives"
    if not tasksets_dir.is_dir():
        return []
    statuses: list[str] = []
    for path in sorted(tasksets_dir.glob("TASKSET-*.md")):
        meta, _body = backlog_board.parse_frontmatter(
            path.read_text(encoding="utf-8")
        )
        if str(meta.get("work_id") or "").strip() == task_set_id:
            statuses.append(str(meta.get("status") or "").strip())
    return statuses


def _effective_taskset_id(
    root: Path,
    *,
    task_id: str,
    requested_taskset_id: str,
) -> tuple[str, list[str]]:
    """Resolve a missing taskset from the task and reject identity drift."""
    requested = str(requested_taskset_id or "").strip()
    tasks = backlog_board.load_tasks(
        root / "agents" / "lead_engineer" / "tasks"
    )
    matches = [task for task in tasks if task.task_id == task_id]
    if len(matches) != 1:
        return requested, []
    actual = str(matches[0].task_set_id or "").strip()
    if requested and actual != requested:
        return requested, [
            f"task-taskset-mismatch:{actual or 'missing'}:{requested}"
        ]
    return requested or actual, []


def _claim_readiness_findings(
    root: Path,
    *,
    task_id: str,
    task_set_id: str,
    unit_id: str,
    unit_spec: str,
) -> list[str]:
    """Return pre-persistence readiness findings for every claim entry point."""
    findings: list[str] = []
    tasks = backlog_board.load_tasks(
        root / "agents" / "lead_engineer" / "tasks"
    )
    task_matches = [task for task in tasks if task.task_id == task_id]
    if len(task_matches) > 1:
        findings.append(f"task:duplicate-id:{task_id}")
    elif not task_matches:
        findings.append(f"task:not-found:{task_id}")
    else:
        task_status = str(task_matches[0].status or "").strip()
        if status_alias.is_blocked(task_status):
            findings.append(f"task:blocked-status:{task_status}")
        actual_taskset = str(task_matches[0].task_set_id or "").strip()
        if task_set_id and actual_taskset != task_set_id:
            findings.append(
                f"task-taskset-mismatch:{actual_taskset or 'missing'}:"
                f"{task_set_id}"
            )

    taskset_statuses = (
        _canonical_taskset_statuses(root, task_set_id) if task_set_id else []
    )
    if len(taskset_statuses) > 1:
        findings.append(f"taskset:duplicate-id:{task_set_id}")
    elif taskset_statuses and status_alias.is_blocked(taskset_statuses[0]):
        findings.append(f"taskset:blocked-status:{taskset_statuses[0]}")

    units = task_unit_readiness_gate.load_unit_specs(root)
    task_units = [
        unit
        for unit in units
        if str(unit[1].get("task_id") or "").strip() == task_id
    ]
    if not unit_id and not unit_spec and not task_units:
        return list(dict.fromkeys(findings))
    if not task_set_id:
        findings.append("unit:missing-taskset-id")

    spec_matches: list[tuple[Path, dict[str, Any], str]] = []
    if unit_spec:
        spec_path = Path(unit_spec)
        if not spec_path.is_absolute():
            spec_path = root / spec_path
        resolved_spec = spec_path.resolve()
        spec_matches = [
            unit for unit in units if unit[0].resolve() == resolved_spec
        ]
        if not spec_matches:
            findings.append(f"unit:spec-not-registered:{unit_spec}")
        elif len(spec_matches) > 1:
            findings.append(f"unit:duplicate-spec:{unit_spec}")
        else:
            spec_meta = spec_matches[0][1]
            spec_task = str(spec_meta.get("task_id") or "").strip()
            spec_unit = str(spec_meta.get("unit_id") or "").strip()
            if spec_task != task_id:
                findings.append(
                    f"unit-spec-task-mismatch:{spec_task or 'missing'}:{task_id}"
                )
            if unit_id and spec_unit != unit_id:
                findings.append(
                    f"unit-spec-id-mismatch:{spec_unit or 'missing'}:{unit_id}"
                )

    readiness_unit_id = unit_id
    if not readiness_unit_id and len(spec_matches) == 1:
        readiness_unit_id = str(spec_matches[0][1].get("unit_id") or "").strip()
    gate_findings = task_unit_readiness_gate.check_root(
        root,
        task_id=task_id,
        unit_id=readiness_unit_id,
        require_ready=True,
    )
    selected_for_readiness = task_units
    if readiness_unit_id:
        selected_for_readiness = [
            unit
            for unit in task_units
            if str(unit[1].get("unit_id") or "").strip() == readiness_unit_id
        ]
    localized_ready_statuses = {
        str(meta.get("status") or "").strip()
        for _path, meta, _body in selected_for_readiness
        if status_alias.normalize_status(meta.get("status"))
        in task_unit_readiness_gate.READY_STATUSES
    }
    for finding in gate_findings:
        if any(
            finding.endswith(f"unit:not-worker-ready:{ready_status}")
            for ready_status in localized_ready_statuses
        ):
            continue
        findings.append(finding)

    selected = [
        meta
        for _path, meta, _body in units
        if (
            not readiness_unit_id
            or str(meta.get("unit_id") or "").strip() == readiness_unit_id
        )
        and str(meta.get("task_id") or "").strip() == task_id
    ]
    for meta in selected:
        unit_taskset = str(meta.get("task_set_id") or "").strip()
        if task_set_id and unit_taskset != task_set_id:
            findings.append(
                f"unit-taskset-mismatch:{unit_taskset}:{task_set_id}"
            )
    return list(dict.fromkeys(findings))


def _security_service_refusal(
    root: Path,
    task_id: str,
    unit_id: str,
    unit_spec: str,
    target_files: list[str],
) -> bool:
    """Run the profile gate only when the security-service asset is installed."""

    scripts = root / "scripts"
    gate = scripts / "security_service_gate.py"
    try:
        scripts_before = scripts.lstat()
    except FileNotFoundError:
        return _missing_security_service_gate_refusal(root)
    except OSError:
        print(
            "security-service claim gate is unavailable, drifted, or not a "
            "regular managed file; "
            "claim creation refused",
            file=sys.stderr,
        )
        return True
    if stat.S_ISLNK(scripts_before.st_mode) or not stat.S_ISDIR(
        scripts_before.st_mode
    ):
        print(
            "security-service claim gate is unavailable, drifted, or not a "
            "regular managed file; claim creation refused",
            file=sys.stderr,
        )
        return True
    try:
        gate_before = gate.lstat()
    except FileNotFoundError:
        try:
            scripts_after = scripts.lstat()
        except OSError:
            scripts_after = None
        if (
            scripts_after is not None
            and (scripts_before.st_dev, scripts_before.st_ino, scripts_before.st_mode)
            == (scripts_after.st_dev, scripts_after.st_ino, scripts_after.st_mode)
        ):
            return _missing_security_service_gate_refusal(root)
        print(
            "security-service claim gate is unavailable, drifted, or not a "
            "regular managed file; claim creation refused",
            file=sys.stderr,
        )
        return True
    except OSError:
        gate_before = None

    gate_source: str | None = None
    if (
        gate_before is not None
        and not stat.S_ISLNK(gate_before.st_mode)
        and stat.S_ISREG(gate_before.st_mode)
        and gate_before.st_size <= SECURITY_SERVICE_GATE_MAX_BYTES
    ):
        try:
            with gate.open("rb") as handle:
                opened_before = os.fstat(handle.fileno())
                payload = handle.read(SECURITY_SERVICE_GATE_MAX_BYTES + 1)
                opened_after = os.fstat(handle.fileno())
            gate_after = gate.lstat()
            scripts_after = scripts.lstat()
            gate_signature = (
                gate_before.st_dev,
                gate_before.st_ino,
                gate_before.st_mode,
                gate_before.st_size,
                gate_before.st_mtime_ns,
            )
            if (
                len(payload) <= SECURITY_SERVICE_GATE_MAX_BYTES
                and gate_signature
                == (
                    opened_before.st_dev,
                    opened_before.st_ino,
                    opened_before.st_mode,
                    opened_before.st_size,
                    opened_before.st_mtime_ns,
                )
                == (
                    opened_after.st_dev,
                    opened_after.st_ino,
                    opened_after.st_mode,
                    opened_after.st_size,
                    opened_after.st_mtime_ns,
                )
                == (
                    gate_after.st_dev,
                    gate_after.st_ino,
                    gate_after.st_mode,
                    gate_after.st_size,
                    gate_after.st_mtime_ns,
                )
                and (
                    scripts_before.st_dev,
                    scripts_before.st_ino,
                    scripts_before.st_mode,
                )
                == (
                    scripts_after.st_dev,
                    scripts_after.st_ino,
                    scripts_after.st_mode,
                )
                and hashlib.sha256(payload).hexdigest()
                == SECURITY_SERVICE_GATE_SHA256
            ):
                gate_source = payload.decode("utf-8")
        except (OSError, UnicodeError):
            gate_source = None
    if gate_source is None:
        print(
            "security-service claim gate is unavailable, drifted, or not a "
            "regular managed file; claim creation refused",
            file=sys.stderr,
        )
        return True
    if (
        not str(task_id or "").strip()
        or not str(unit_id or "").strip()
        or not str(unit_spec or "").strip()
    ):
        print(
            "security-service profile requires registered task and unit identities "
            "plus a canonical unit specification; "
            "claim creation refused",
            file=sys.stderr,
        )
        return True
    command = [
        sys.executable,
        "-c",
        SECURITY_SERVICE_GATE_BOOTSTRAP,
        str(gate),
        "--root",
        str(root),
        "--task-id",
        str(task_id),
        "--unit-id",
        str(unit_id),
        "--unit-spec",
        str(unit_spec),
    ]
    for path in target_files:
        command.extend(["--target-file", path])
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input=gate_source,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        print(
            "security-service claim gate unavailable; claim creation refused",
            file=sys.stderr,
        )
        return True
    if result.returncode == 0:
        return False
    detail = (result.stderr or result.stdout).strip()
    print("security-service claim gate refused claim creation", file=sys.stderr)
    if detail:
        print(detail, file=sys.stderr)
    return True


def _stable_profile_state_text(path: Path) -> str:
    try:
        before = path.lstat()
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or before.st_size > SECURITY_SERVICE_PROFILE_STATE_MAX_BYTES
            or before.st_mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) == 0
        ):
            raise ValueError("profile state is unavailable or malformed")
        with path.open("rb") as handle:
            opened_before = os.fstat(handle.fileno())
            payload = handle.read(SECURITY_SERVICE_PROFILE_STATE_MAX_BYTES + 1)
            opened_after = os.fstat(handle.fileno())
        after = path.lstat()
    except OSError as exc:
        raise ValueError("profile state is unavailable or malformed") from exc
    signatures = {
        (
            item.st_dev,
            item.st_ino,
            item.st_mode,
            item.st_size,
            item.st_mtime_ns,
        )
        for item in (before, opened_before, opened_after, after)
    }
    if len(payload) > SECURITY_SERVICE_PROFILE_STATE_MAX_BYTES or len(signatures) != 1:
        raise ValueError("profile state changed while it was read")
    try:
        return payload.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("profile state is unavailable or malformed") from exc


def _profile_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value[0] in {"'", '"'}:
        quote = value[0]
        end = value.find(quote, 1)
        if end < 0:
            raise ValueError("profile scalar has an unterminated quote")
        trailing = value[end + 1 :].strip()
        if trailing and not trailing.startswith("#"):
            raise ValueError("profile scalar has unsupported trailing content")
        return value[1:end]
    match = re.fullmatch(r"([^#]*?)(?:\s+#.*)?", value)
    if match is None:
        raise ValueError("profile scalar is malformed")
    return match.group(1).strip()


def _config_selects_security_service(root: Path) -> bool:
    primary = root / "agent_runtime.yml"
    legacy = root / "ralph.yml"
    try:
        primary.lstat()
        config = primary
    except FileNotFoundError:
        try:
            legacy.lstat()
            config = legacy
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise ValueError("profile configuration is unavailable") from exc
    except OSError as exc:
        raise ValueError("profile configuration is unavailable") from exc

    text = _stable_profile_state_text(config)
    schema: str | None = None
    schema_seen = False
    profiles_seen = False
    in_profiles = False
    profiles: list[str] = []
    for raw_line in text.splitlines():
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise ValueError("profile configuration uses tab indentation")
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation == 0:
            if ":" not in stripped:
                raise ValueError("profile configuration has malformed top level")
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            if key == "schema":
                if schema_seen:
                    raise ValueError("profile configuration repeats schema")
                schema = _profile_scalar(raw_value)
                schema_seen = True
                in_profiles = False
            elif key == "profiles":
                if profiles_seen or _profile_scalar(raw_value):
                    raise ValueError("profile configuration has malformed profiles")
                profiles_seen = True
                in_profiles = True
            else:
                in_profiles = False
            continue
        if in_profiles:
            if indentation != 2 or not stripped.startswith("- "):
                raise ValueError("profile configuration has malformed profiles")
            profile = _profile_scalar(stripped[2:])
            if profile not in {
                "core",
                "web-content",
                "security-service",
                "full-runtime",
            }:
                raise ValueError("profile configuration has an unknown profile")
            profiles.append(profile)

    if schema_seen and schema != "agent-runtime-config/v2":
        raise ValueError("profile configuration has an unsupported schema")
    if not schema_seen:
        return True
    unique_profiles = tuple(dict.fromkeys(profiles))
    if "full-runtime" in unique_profiles:
        if len(unique_profiles) != 1:
            raise ValueError("full-runtime cannot be combined with another profile")
        return True
    return "security-service" in unique_profiles


def _lock_selects_security_service(root: Path) -> bool:
    lock = root / "agent_runtime.lock.json"
    try:
        lock.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ValueError("profile lock is unavailable") from exc
    try:
        payload = json.loads(_stable_profile_state_text(lock))
    except json.JSONDecodeError as exc:
        raise ValueError("profile lock is malformed") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != "agent-runtime-lock/v2"
        or not isinstance(payload.get("profiles"), list)
        or not all(isinstance(item, str) for item in payload["profiles"])
    ):
        raise ValueError("profile lock is malformed")
    profiles = payload["profiles"]
    if any(
        profile not in {"core", "web-content", "security-service"}
        for profile in profiles
    ):
        raise ValueError("profile lock contains an unknown profile")
    return "security-service" in profiles


def _security_service_expected(root: Path) -> bool:
    for relative in SECURITY_SERVICE_PROFILE_MARKERS:
        marker = root / relative
        try:
            marker.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError("security-service marker is unavailable") from exc
        return True
    return _lock_selects_security_service(root) or _config_selects_security_service(
        root
    )


def _missing_security_service_gate_refusal(root: Path) -> bool:
    try:
        expected = _security_service_expected(root)
    except ValueError:
        print(
            "security-service profile state is unavailable or malformed; "
            "claim creation refused",
            file=sys.stderr,
        )
        return True
    if not expected:
        return False
    print(
        "security-service claim gate is missing from a selected or partially "
        "installed profile; claim creation refused",
        file=sys.stderr,
    )
    return True


def _claim_store_refusal(
    operation: str,
    inspection: Any,
) -> int:
    detail = str(inspection.finding or "claim-store state is not writable")
    detail = " ".join(detail.split())[:256]
    print(
        f"claim-store {operation} refused ({inspection.state}): {detail}",
        file=sys.stderr,
    )
    return 1


def _prepare_create(
    args: argparse.Namespace,
    *,
    emit_success: bool = True,
) -> int | _CreatePreparation:
    """Resolve every non-claim-store create gate without mutating the host."""

    root = args.root.resolve()
    errors = _validate_create_args(args)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    task_set_id, binding_findings = _effective_taskset_id(
        root,
        task_id=args.task_id,
        requested_taskset_id=str(args.task_set_id or "").strip(),
    )
    if binding_findings:
        for finding in binding_findings:
            print(f"claim-preflight:readiness:{finding}", file=sys.stderr)
        return 1
    strict_claim_preflight = _structured_claim_preflight_expected(
        root, args.task_id
    )
    if task_set_id and _plan_check_refusal(
        root,
        task_set_id,
        skip_plan_check=args.skip_plan_check,
        require_snapshot=strict_claim_preflight,
        emit_success=emit_success,
    ):
        return 1
    if strict_claim_preflight:
        readiness_findings = _claim_readiness_findings(
            root,
            task_id=args.task_id,
            task_set_id=task_set_id,
            unit_id=str(args.unit_id or "").strip(),
            unit_spec=str(args.unit_spec or "").strip(),
        )
        if readiness_findings:
            for finding in readiness_findings:
                print(f"claim-preflight:readiness:{finding}", file=sys.stderr)
            return 1

    explicit_targets = _normalize_target_files(tuple(args.target_file or ()))
    if _security_service_refusal(
        root,
        args.task_id,
        args.unit_id,
        args.unit_spec,
        explicit_targets,
    ):
        return 1
    try:
        defect_signatures, knowledge_matches = _knowledge_lookup(root, args)
    except compound_record.CompoundRecordError as exc:
        print("compound knowledge lookup failed before claim persistence:", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    escalation_triggers = _resolve_escalation_triggers(root, args)
    target_files = _resolve_target_files(root, args)
    try:
        token_budgets = _resolve_token_budgets(root, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return _CreatePreparation(
        task_set_id=task_set_id,
        strict_claim_preflight=strict_claim_preflight,
        target_files=tuple(target_files),
        escalation_triggers=tuple(escalation_triggers),
        routing_decision=_resolve_claim_routing(
            root, args, escalation_triggers
        ),
        token_budgets=token_budgets,
        defect_signatures=tuple(defect_signatures),
        knowledge_matches=tuple(knowledge_matches),
    )


def cmd_create(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        claim_now, claim_expires_at = _claim_lease_window(args)
        inspection = claim_store.inspect_store(root)
        if inspection.state not in {"pristine", "initialized"}:
            return _claim_store_refusal("create", inspection)
        records = _read_claims(root)
        active_path = _active_task_claim_path(records, args.task_id)
        if active_path is not None:
            print(
                f"task already has an active claim: {args.task_id} "
                f"({_rel(root, active_path)})",
                file=sys.stderr,
            )
            return 1
        preflight = _prepare_create(args, emit_success=False)
        if isinstance(preflight, int):
            return preflight
        with claim_store.store_lock(root):
            inspection = claim_store.inspect_store(root)
            if inspection.state not in {"pristine", "initialized"}:
                return _claim_store_refusal("create", inspection)
            preparation = _prepare_create(args)
            if isinstance(preparation, int):
                return preparation
            if (
                preflight.task_set_id != preparation.task_set_id
                or preflight.strict_claim_preflight
                != preparation.strict_claim_preflight
            ):
                print(
                    "claim-preflight:readiness:authority-changed-while-locking; "
                    "retry claim creation",
                    file=sys.stderr,
                )
                return 1
            args.task_set_id = preparation.task_set_id
            outcome = _cmd_create_locked(
                args,
                store_inspection=inspection,
                preparation=preparation,
                now=claim_now,
                expires_at=claim_expires_at,
            )
    except (
        claim_store.ClaimStoreError,
        TimeoutError,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        detail = " ".join(str(exc).split())[:256] or "claim-store unavailable"
        print(f"claim-store create refused: {detail}", file=sys.stderr)
        return 1
    if isinstance(outcome, int):
        return outcome
    claim, claim_dir, claim_path, claim_commit_authorized = outcome
    return _complete_create(
        args,
        claim=claim,
        claim_dir=claim_dir,
        claim_path=claim_path,
        claim_commit_authorized=claim_commit_authorized,
    )


def _cmd_create_locked(
    args: argparse.Namespace,
    *,
    store_inspection: Any,
    preparation: _CreatePreparation,
    now: datetime,
    expires_at: datetime,
) -> int | tuple[dict[str, Any], Path, Path, bool]:
    root = args.root.resolve()
    records = _read_claims(root)
    active_path = _active_task_claim_path(records, args.task_id)
    if active_path is not None:
        print(
            f"task already has an active claim: {args.task_id} "
            f"({_rel(root, active_path)})",
            file=sys.stderr,
        )
        return 1
    claim_commit_authorized = _claim_autocommit_enabled(
        cli_opt_in=args.commit_claim_artifacts
    )
    claim = _build_claim(
        args,
        records,
        now=now,
        expires_at=expires_at,
        target_files=list(preparation.target_files),
        escalation_triggers=list(preparation.escalation_triggers),
        routing_decision=preparation.routing_decision,
        token_budgets=preparation.token_budgets,
        defect_signatures=list(preparation.defect_signatures),
        knowledge_matches=list(preparation.knowledge_matches),
    )
    claim["mutation_revision"] = 0
    claim["scope_binding"] = _binding_for_claim(
        claim,
        bound_at=str(claim["claimed_at"]),
    )
    claim["persistence"] = {
        "mode": "scm_commit" if claim_commit_authorized else "working_tree",
        "scm_commit_authorized": claim_commit_authorized,
    }
    if not claim_store.valid_claim_id(claim.get("claim_id")):
        print("claim_id must use the canonical CLAIM-* identifier syntax", file=sys.stderr)
        return 1
    for field in ("handoff_path", "log_path"):
        finding = _claim_artifact_ref_error(claim.get(field), field)
        if finding:
            print(finding, file=sys.stderr)
            return 1
    creation_errors = _claim_creation_errors(root, claim, records)
    if creation_errors:
        for error in creation_errors:
            print(error, file=sys.stderr)
        return 1
    footprint_errors, footprint_warnings = _footprint_conflict_errors(root, claim, records)
    for warning in footprint_warnings:
        print(warning, file=sys.stderr)
    if footprint_errors:
        for error in footprint_errors:
            print(error, file=sys.stderr)
        return 1
    print(
        "compound knowledge lookup: "
        f"{len(preparation.knowledge_matches)} match(es) before claim persistence",
        file=sys.stderr,
    )
    for match in preparation.knowledge_matches:
        print(
            f"- {match.get('id')} {match.get('path')}: {match.get('title', '')}",
            file=sys.stderr,
        )
    if not claim_store.verify_snapshot(root, store_inspection.snapshot):
        print(
            "claim-store create refused: authority changed before persistence",
            file=sys.stderr,
        )
        return 1
    claim_dir = _claim_dir(root)
    claim_path = claim_dir / f"{claim['claim_id']}.json"
    artifact_paths = [
        (claim_path, "claim file"),
        (root / str(claim["handoff_path"]), "handoff_path"),
        (root / str(claim["log_path"]), "log_path"),
    ]
    collisions = [
        f"{label} already exists: {_rel(root, candidate)}"
        for candidate, label in artifact_paths
        if _entry_exists(candidate, label)
    ]
    if collisions:
        for collision in collisions:
            print(collision, file=sys.stderr)
        return 1
    handoff_path = root / str(claim["handoff_path"])
    log_path = root / str(claim["log_path"])
    handoff_text = "\n".join(
        [
            f"# Handoff: {claim['display_name']}",
            "",
            f"- claim_id: {claim['claim_id']}",
            f"- task_id: {claim['task_id']}",
            f"- worktree_path: {claim['worktree_path']}",
            f"- branch: {claim['branch']}",
            f"- task_set_id: {claim['task_set_id']}",
            f"- project_id: {claim['project_id']}",
            f"- unit_id: {claim['unit_id']}",
            f"- unit_spec: {claim['unit_spec']}",
            f"- requested_model_tier: {claim['requested_model_tier']}",
            f"- selected_model_tier: {claim['selected_model_tier']}",
            f"- model_tier: {claim['model_tier']}",
            f"- routing_status: {claim['routing_status']}",
            f"- wip_slot: {claim['wip_slot']}",
            f"- stop_condition: {claim['stop_condition']}",
            f"- phase: {claim['phase']}",
            f"- step: {claim['step_index']}/{claim['step_total']}",
            f"- progress_pct: {claim['progress_pct']}",
            f"- status_text: {claim['status_text']}",
            "- status: claimed",
            "",
        ]
    )
    log_text = "\n".join(
        [
            f"# Claim Log: {claim['display_name']}",
            "",
            f"- claimed_at: {claim['claimed_at']}",
            f"- agent_instance_id: {claim['agent_instance_id']}",
            f"- callsite_id: {claim['callsite_id']}",
            f"- task_set_id: {claim['task_set_id']}",
            f"- project_id: {claim['project_id']}",
            f"- unit_id: {claim['unit_id']}",
            f"- unit_spec: {claim['unit_spec']}",
            f"- requested_model_tier: {claim['requested_model_tier']}",
            f"- selected_model_tier: {claim['selected_model_tier']}",
            f"- model_tier: {claim['model_tier']}",
            f"- routing_status: {claim['routing_status']}",
            f"- wip_slot: {claim['wip_slot']}",
            f"- stop_condition: {claim['stop_condition']}",
            f"- status_text: {claim['status_text']}",
            "",
        ]
    )
    claim_bytes = (
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    intended_publications = (
        (handoff_path, handoff_text.encode("utf-8")),
        (log_path, log_text.encode("utf-8")),
        (claim_path, claim_bytes),
    )
    publications: list[_CreatedPublication] = []
    missing_directories = tuple(_missing_directories(claim_dir, root))
    try:
        handoff_identity = _ensure_text_file(handoff_path, handoff_text)
        publications.append(
            _created_publication(
                *intended_publications[0],
                handoff_identity,
            )
        )
        log_identity = _ensure_text_file(log_path, log_text)
        publications.append(
            _created_publication(
                *intended_publications[1],
                log_identity,
            )
        )
        claim_identity = atomic_io.publish_json_owned_atomic(claim_path, claim)
        publications.append(
            _created_publication(
                *intended_publications[2],
                claim_identity,
            )
        )
        if store_inspection.state == "pristine":
            claim_store.initialize_store(
                root,
                witness_claim_id=str(claim["claim_id"]),
            )
    except Exception as exc:
        rollback_findings = _rollback_claim_creation(
            root,
            claim_id=str(claim["claim_id"]),
            publications=tuple(publications),
            pristine_store=store_inspection.state == "pristine",
            missing_directories=missing_directories,
        )
        if rollback_findings:
            raise RuntimeError(
                "claim creation rollback incomplete: " + "; ".join(rollback_findings)
            ) from exc
        raise
    return claim, claim_dir, claim_path, claim_commit_authorized


def _add_post_commit_warning(
    warnings: list[dict[str, str]],
    *,
    stage: str,
    error: BaseException,
) -> None:
    reason = " ".join(str(error).split())[:256] or type(error).__name__
    warnings.append({"stage": stage, "reason": reason})
    print(
        f"warning: claim authority persisted but {stage} failed: {reason}",
        file=sys.stderr,
    )


def _complete_create(
    args: argparse.Namespace,
    *,
    claim: dict[str, Any],
    claim_dir: Path,
    claim_path: Path,
    claim_commit_authorized: bool,
) -> int:
    """Run non-authoritative effects after the claim-store lock is released."""

    root = args.root.resolve()
    post_commit_warnings: list[dict[str, str]] = []
    try:
        record_claim_instance(root, claim, claim_path=claim_path)
    except Exception as exc:  # noqa: BLE001 - claim authority is already durable
        _add_post_commit_warning(
            post_commit_warnings,
            stage="agent-instance-registry",
            error=exc,
        )
    try:
        append_event(
            root,
            {
                "event": "claim_created",
                "actor": claim["agent_instance_id"],
                "actor_role": claim["agent_role"],
                "agent_instance_id": claim["agent_instance_id"],
                "display_name": claim["display_name"],
                "callsite_id": claim["callsite_id"],
                "task_id": claim["task_id"],
                "task_set_id": claim["task_set_id"],
                "claim_id": claim["claim_id"],
                "worktree_path": claim["worktree_path"],
                "message": claim["status_text"],
                "ts": claim["claimed_at"],
            },
        )
    except Exception as exc:  # noqa: BLE001 - claim authority is already durable
        _add_post_commit_warning(
            post_commit_warnings,
            stage="claim-created-event",
            error=exc,
        )
    # Live A2A traffic: a real claim create opens the request->review->decision->
    # correction lifecycle on the runtime message stream. Additive observability
    # only — it RECORDS, it never changes who gets the claim, and a failure here
    # must never break claim creation (the emitter swallows its own errors).
    if a2a_claim_emitter is not None:
        try:
            a2a_claim_emitter.emit_claim_request(claim, root=root)
        except Exception as exc:  # noqa: BLE001 - additive observability only
            _add_post_commit_warning(
                post_commit_warnings,
                stage="claim-created-a2a",
                error=exc,
            )
    # Crash-safety guard: commit the claim immediately so a sibling session's
    # `git reset --hard` / `git clean -fd` cannot erase an untracked claim
    # (incident 2026-06-12). Best-effort — never fails claim creation.
    persistence_result: dict[str, Any] | None = None
    if claim_commit_authorized:
        try:
            persistence_result = claim_guard.commit_claim_artifacts(
                root,
                claim_path,
                extra_paths=[
                    claim_dir / ".claim-store",
                    root / str(claim["handoff_path"]),
                    root / str(claim["log_path"]),
                ],
                claim_id=str(claim["claim_id"]),
            )
        except Exception as exc:  # noqa: BLE001 - claim authority is durable
            _add_post_commit_warning(
                post_commit_warnings,
                stage="claim-artifact-scm-persistence",
                error=exc,
            )
        if (
            persistence_result is not None
            and not persistence_result.get("ok")
            and persistence_result.get("reason") != "not-a-git-repo"
        ):
            if persistence_result.get("committed"):
                print(
                    f"error: claim {claim['claim_id']} was published but could "
                    "not be verified "
                    f"({persistence_result.get('reason')}); DO NOT RETRY this "
                    "claim commit and stop for operator recovery",
                    file=sys.stderr,
                )
            else:
                print(
                    f"warning: claim {claim['claim_id']} was not committed "
                    f"({persistence_result.get('reason')}); an untracked claim "
                    "can be lost by a concurrent 'git reset --hard'/'git clean -fd'",
                    file=sys.stderr,
                )
    response = {
        "status": "created",
        "path": _rel(root, claim_path),
        "claim": claim,
    }
    if post_commit_warnings:
        response["post_commit_warnings"] = post_commit_warnings
    if persistence_result is not None:
        response["persistence_result"] = persistence_result
    if (
        persistence_result is not None
        and not persistence_result.get("ok")
        and persistence_result.get("committed")
    ):
        response["status"] = "created_published_unverified"
        _emit(response, as_json=args.json)
        return 1
    _emit(response, as_json=args.json)
    return 0


def _find_claim(root: Path, claim_id: str) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in _read_claims(root):
        if str(payload.get("claim_id") or "") == claim_id:
            return path, payload
    return None


def _find_claim_in_canonical_snapshot(
    root: Path,
    claim_id: str,
) -> tuple[Path, dict[str, Any]] | None:
    """Resolve one claim from the locked, verified store snapshot."""

    for payload in claim_store.read_claims_snapshot(root):
        if str(payload.get("claim_id") or "") != claim_id:
            continue
        path = _claim_dir(root) / f"{claim_id}.json"
        return path, dict(payload)
    return None


def _parse_aware_timestamp(value: object, label: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} timestamp is missing")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} timestamp is malformed") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} timestamp must be timezone-aware")
    return parsed


def _mutation_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc).astimezone()
    return _parse_aware_timestamp(value, "now")


def _claim_temporal_fields(
    claim: dict[str, Any],
) -> tuple[datetime, datetime]:
    lease = claim.get("lease")
    if not isinstance(lease, dict):
        raise ValueError("claim lease timestamps are missing")
    heartbeat = _parse_aware_timestamp(
        claim.get("last_heartbeat"),
        "last_heartbeat",
    )
    nested_heartbeat = _parse_aware_timestamp(
        lease.get("heartbeat_at"),
        "lease heartbeat",
    )
    if heartbeat != nested_heartbeat:
        raise ValueError("claim heartbeat timestamp copies do not match")
    expires = _parse_aware_timestamp(claim.get("expires_at"), "expires_at")
    nested_expires = _parse_aware_timestamp(
        lease.get("expires_at"),
        "lease expires_at",
    )
    if expires != nested_expires:
        raise ValueError("claim expires timestamp copies do not match")
    return heartbeat, expires


def _validate_progress_update(args: argparse.Namespace) -> dict[str, Any] | None:
    values = {field: getattr(args, field, None) for field in PROGRESS_FIELDS}
    present = [value is not None for value in values.values()]
    if any(present) and not all(present):
        raise ValueError(
            "progress update requires phase, progress_pct, step_index, "
            "step_total, and status_text together"
        )
    if not any(present):
        return None
    phase = str(values["phase"] or "").strip()
    status_text = str(values["status_text"] or "").strip()
    progress_pct = values["progress_pct"]
    step_index = values["step_index"]
    step_total = values["step_total"]
    if not phase or not status_text:
        raise ValueError("progress phase and status_text must be non-empty")
    if type(progress_pct) is not int or not 0 <= progress_pct <= 100:
        raise ValueError("progress_pct must be between 0 and 100")
    if type(step_total) is not int or step_total < 1:
        raise ValueError("step_total must be at least 1")
    if type(step_index) is not int or not 1 <= step_index <= step_total:
        raise ValueError("step_index must be between 1 and step_total")
    if phase.lower() in COMPLETION_PHASES and (
        step_index != step_total or progress_pct != 100
    ):
        raise ValueError(
            "completion phase requires final step and 100 percent progress"
        )
    return {
        "phase": phase,
        "progress_pct": progress_pct,
        "step_index": step_index,
        "step_total": step_total,
        "status_text": status_text,
    }


def _validate_mutation_authority(
    claim: dict[str, Any],
    args: argparse.Namespace,
    *,
    operation: str,
    now: datetime,
) -> tuple[datetime, datetime, int]:
    if not _is_active(claim):
        raise ValueError("claim mutation requires an active claim")
    if _is_explicit_overlay(claim) and operation != "heartbeat":
        raise ValueError("claim scope renewal does not apply to an overlay claim")
    if str(claim.get("agent_instance_id") or "") != args.agent_instance_id:
        raise ValueError("claim owner does not match agent_instance_id")
    if str(claim.get("callsite_id") or "") != args.callsite_id:
        raise ValueError("claim callsite does not match callsite_id")
    revision = claim.get("mutation_revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("claim mutation revision is invalid")
    if revision != args.expected_revision:
        raise ValueError(
            f"claim revision mismatch: expected {args.expected_revision}, "
            f"observed {revision}"
        )
    heartbeat, expires = _claim_temporal_fields(claim)
    liveness = claim_store.classify_claim_liveness(claim, now=now)
    if liveness.state == "expired":
        raise ValueError("claim lease is expired")
    if liveness.state != "live":
        raise ValueError(
            f"claim lease is indeterminate: {liveness.reason}"
        )
    if now <= heartbeat:
        raise ValueError("heartbeat timestamp must be strictly increasing")
    return heartbeat, expires, revision


def _persisted_scope_binding(claim: dict[str, Any]) -> dict[str, Any]:
    binding = claim.get("scope_binding")
    if not isinstance(binding, dict):
        raise ValueError("claim scope binding is missing")
    bound_at = binding.get("bound_at")
    if not isinstance(bound_at, str) or not bound_at.strip():
        raise ValueError("claim scope binding bound_at is invalid")
    expected = _binding_for_claim(claim, bound_at=bound_at)
    if binding != expected:
        raise ValueError("claim scope binding is invalid")
    return json.loads(json.dumps(binding, ensure_ascii=False))


def _current_scope_values(
    root: Path,
    claim: dict[str, Any],
) -> tuple[list[str], str]:
    unit_spec = str(claim.get("unit_spec") or "").strip()
    if not unit_spec:
        return (
            _normalize_target_files(tuple(claim.get("target_files") or ())),
            str(claim.get("stop_condition") or ""),
        )
    direct_ref = _direct_repo_file_ref(root, unit_spec, "unit_spec")
    meta = _unit_meta(root, direct_ref)
    if str(meta.get("task_id") or "").strip() != str(
        claim.get("task_id") or ""
    ):
        raise ValueError("unit_spec task identity changed")
    if str(meta.get("unit_id") or "").strip() != str(
        claim.get("unit_id") or ""
    ):
        raise ValueError("unit_spec unit identity changed")
    return (
        _unit_spec_target_files(root, direct_ref),
        _unit_spec_stop_condition(root, direct_ref),
    )


def _accepted_replan_ref(
    root: Path,
    claim: dict[str, Any],
    value: str,
) -> str:
    replan_ref = _direct_repo_file_ref(root, value, "replan_ref")
    if not replan_ref:
        raise ValueError("scope drift requires an accepted direct replan")
    meta = _work_item_meta(root / replan_ref)
    if str(meta.get("status") or "").strip().lower() != "accepted":
        raise ValueError("replan review must have accepted status")
    if str(meta.get("signal") or "").strip().lower() != "pass":
        raise ValueError("replan review must have pass signal")
    if str(meta.get("tier") or "").strip().upper() not in {"T2", "T3"}:
        raise ValueError("replan review must be tier T2 or T3")
    if str(meta.get("task_id") or "").strip() != str(
        claim.get("task_id") or ""
    ):
        raise ValueError("replan review task identity does not match claim")
    if str(meta.get("unit_id") or "").strip() != str(
        claim.get("unit_id") or ""
    ):
        raise ValueError("replan review unit identity does not match claim")

    registry = plan_assumption_gate._load_registry(root)  # noqa: SLF001
    if not isinstance(registry, dict) or registry.get("schema") != plan_assumption_gate.SCHEMA:
        raise ValueError("replan plan-assumption registry is invalid")
    task_set_id = str(claim.get("task_set_id") or "").strip()
    entries = [
        entry
        for entry in registry.get("assumption_sets", [])
        if isinstance(entry, dict)
        and str(entry.get("taskset_id") or "").strip() == task_set_id
    ]
    if len(entries) != 1:
        raise ValueError("replan plan-assumption entry is missing or duplicated")
    entry = entries[0]
    if str(entry.get("design_record") or "").strip() != replan_ref:
        raise ValueError("replan must be the direct plan design_record")
    if str(entry.get("revalidation_policy") or "").strip() != "block_dispatch_on_drift":
        raise ValueError("replan must block dispatch on drift")
    anchors = entry.get("anchors")
    if not isinstance(anchors, list) or not anchors:
        raise ValueError("replan plan-assumption anchors are missing")
    findings = _strict_plan_assumption_findings(root, task_set_id)
    if findings:
        raise ValueError("replan plan-assumption anchors are invalid or drifted")
    return replan_ref


def _projection_payload(
    root: Path,
    path: Path,
    claim: dict[str, Any],
    *,
    include_revision: bool,
) -> dict[str, Any]:
    rel_path = _rel(root, path)
    pointer_agent_fields = tuple(
        field
        for field in claim_store.POINTER_AGENT_FIELDS
        if field not in {"claim_path", "handoff_path", "log_path", "last_heartbeat"}
    )
    agent = {
        key: claim.get(key)
        for key in pointer_agent_fields
        + (
            "requested_model_tier",
            "selected_model_tier",
            "routing_policy_id",
            "routing_escalation_reason",
            "task_token_budget",
            "claim_token_budget",
        )
    }
    agent.update(
        {
            "claim_path": rel_path,
            "handoff_path": claim.get("handoff_path"),
            "log_path": claim.get("log_path"),
            "last_heartbeat": claim.get("last_heartbeat"),
        }
    )
    if include_revision:
        agent["mutation_revision"] = claim.get("mutation_revision", 0)
    return {
        "status": "projection",
        "operation": "merge",
        "claim_id": claim.get("claim_id"),
        "claim_revision": claim.get("mutation_revision", 0),
        "task_claim_ref": rel_path,
        "task_id": claim.get("task_id"),
        "unit_id": claim.get("unit_id"),
        "task_set_id": claim.get("task_set_id"),
        "pointer": {
            "active_task": claim.get("task_id"),
            "active_task_set": claim.get("task_set_id"),
            "active_claims": [rel_path],
            "current_agents": [agent],
        },
    }


def cmd_projection(args: argparse.Namespace) -> int:
    """Emit the deterministic active-work projection required after dispatch.

    The dispatcher remains claim-only: generated board and canonical work-item
    writes belong to the serial projection owner.  This command prevents the
    former scalar-ID workaround by giving that owner the exact task/unit refs
    and complete ``current_agents`` record to project.
    """
    root = args.root.resolve()
    try:
        found = _find_claim_in_canonical_snapshot(root, args.claim_id)
        if found is None:
            raise ValueError(f"claim not found: {args.claim_id}")
        path, claim = found
        if not _is_active(claim):
            raise ValueError(
                f"projection requires an active worker claim: {args.claim_id}"
            )
        if _is_explicit_overlay(claim):
            raise ValueError(
                f"projection does not apply to overlay claim: {args.claim_id}"
            )
        now = _mutation_now(args.now)
        liveness = claim_store.classify_claim_liveness(claim, now=now)
        if liveness.state == "expired":
            raise ValueError(f"projection claim is expired: {args.claim_id}")
        if liveness.state != "live":
            raise ValueError(
                f"projection claim liveness is indeterminate: {liveness.reason}"
            )
        projection = _projection_payload(
            root,
            path,
            claim,
            include_revision=True,
        )
    except (
        claim_store.ClaimStoreError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        detail = " ".join(str(exc).split())[:256] or "claim-store unavailable"
        print(f"claim-store projection refused: {detail}", file=sys.stderr)
        return 1
    _emit(projection, as_json=args.json)
    return 0


def _cmd_claim_mutation_locked(
    args: argparse.Namespace,
    *,
    operation: str,
    now: datetime,
    progress: dict[str, Any] | None = None,
    renewal_expires_at: datetime | None = None,
) -> tuple[Path, dict[str, Any], dict[str, Any] | None]:
    root = args.root.resolve()
    inspection = claim_store.inspect_store(root)
    if inspection.state != "initialized" or inspection.snapshot is None:
        raise claim_store.ClaimStoreError(
            inspection.finding or "claim-store authority is not initialized"
        )
    found = _find_claim(root, args.claim_id)
    if found is None:
        raise ValueError(f"claim not found: {args.claim_id}")
    path, claim = found
    heartbeat, expires, revision = _validate_mutation_authority(
        claim,
        args,
        operation=operation,
        now=now,
    )
    now_text = now.isoformat()
    scope_change: dict[str, Any] | None = None
    renewed_targets: list[str] | None = None
    renewed_stop: str | None = None

    if operation == "heartbeat":
        duration = expires - heartbeat
        if duration <= timedelta(0):
            raise ValueError("claim lease duration must be positive")
        try:
            new_expires = now + duration
        except OverflowError:
            raise ValueError("claim lease duration exceeds datetime bounds") from None
    elif operation == "renew":
        if renewal_expires_at is None:
            raise ValueError("renewal lease expiration is missing")
        new_expires = renewal_expires_at
        old_binding = _persisted_scope_binding(claim)
        old_digest = str(old_binding["digest"])
        if str(args.expected_scope_digest or "").strip() != old_digest:
            raise ValueError(
                "claim scope digest mismatch: expected persisted scope binding"
            )
        renewed_targets, renewed_stop = _current_scope_values(root, claim)
        candidate_binding = _binding_for_claim(
            claim,
            bound_at=now_text,
            target_files=renewed_targets,
            stop_condition=renewed_stop,
        )
        changed = str(candidate_binding["digest"]) != old_digest
        replan_ref: str | None = None
        if changed:
            replan_ref = _accepted_replan_ref(root, claim, args.replan_ref)
            new_binding = candidate_binding
        else:
            new_binding = old_binding
        scope_change = {
            "changed": changed,
            "old_digest": old_digest,
            "new_digest": str(new_binding["digest"]),
            "replan_ref": replan_ref,
            "old_scope_binding": old_binding,
            "new_scope_binding": new_binding,
        }
    else:
        raise ValueError(f"unknown claim mutation operation: {operation}")

    updated = json.loads(json.dumps(claim, ensure_ascii=False))
    lease = dict(updated.get("lease") or {})
    expires_text = new_expires.isoformat()
    updated["last_heartbeat"] = now_text
    updated["updated_at"] = now_text
    updated["expires_at"] = expires_text
    lease["heartbeat_at"] = now_text
    lease["expires_at"] = expires_text
    updated["lease"] = lease
    updated["mutation_revision"] = revision + 1
    if progress is not None:
        updated.update(progress)
    if scope_change is not None:
        if scope_change["changed"]:
            assert renewed_targets is not None and renewed_stop is not None
            updated["target_files"] = renewed_targets
            updated["stop_condition"] = renewed_stop
            updated["scope_binding"] = scope_change["new_scope_binding"]
        last_renewal = {
            "renewed_at": now_text,
            "replan_ref": scope_change["replan_ref"],
            "old_scope_binding": scope_change["old_scope_binding"],
            "new_scope_binding": scope_change["new_scope_binding"],
        }
        if len(json.dumps(last_renewal, ensure_ascii=False)) > 4096:
            raise ValueError("renewal scope provenance exceeds the bounded limit")
        updated["last_renewal"] = last_renewal

    if not claim_store.verify_snapshot(root, inspection.snapshot):
        raise claim_store.ClaimStoreError(
            "claim-store authority changed before mutation persistence"
        )
    atomic_io.write_json_atomic(path, updated)
    return path, updated, scope_change


def _mutation_projection_payload(
    root: Path,
    path: Path,
    claim: dict[str, Any],
) -> dict[str, Any]:
    """Return a receipt projection without inventing overlay pointer authority."""

    if not _is_explicit_overlay(claim):
        return _projection_payload(root, path, claim, include_revision=True)
    return {
        "status": "projection",
        "operation": "overlay-no-primary-pointer",
        "claim_id": claim.get("claim_id"),
        "claim_revision": claim.get("mutation_revision", 0),
        "task_claim_ref": _rel(root, path),
        "task_id": claim.get("task_id"),
        "unit_id": claim.get("unit_id"),
        "task_set_id": claim.get("task_set_id"),
    }


def _complete_claim_mutation(
    args: argparse.Namespace,
    *,
    operation: str,
    path: Path,
    claim: dict[str, Any],
    scope_change: dict[str, Any] | None,
) -> int:
    root = args.root.resolve()
    warnings: list[dict[str, str]] = []
    receipt: dict[str, Any] = {
        "committed": True,
        "claim_revision": claim["mutation_revision"],
    }
    if scope_change is not None:
        receipt["scope_change"] = scope_change
    try:
        instance_path, instance = record_claim_instance(
            root,
            claim,
            claim_path=path,
            emit_spawn_event=False,
        )
        receipt["instance"] = {
            "path": _rel(root, instance_path),
            "updated_at": instance.get("updated_at"),
            "last_heartbeat": instance.get("last_heartbeat"),
            "claim_revision": instance.get("claim_revision"),
        }
    except Exception as exc:  # noqa: BLE001 - claim authority is committed
        _add_post_commit_warning(
            warnings,
            stage="agent-instance-registry",
            error=exc,
        )
    try:
        pane_event = append_event(
            root,
            {
                "event": "instance_heartbeat",
                "actor": claim.get("agent_instance_id") or "unknown",
                "actor_role": claim.get("agent_role"),
                "agent_instance_id": claim.get("agent_instance_id"),
                "display_name": claim.get("display_name"),
                "callsite_id": claim.get("callsite_id"),
                "task_id": claim.get("task_id"),
                "task_set_id": claim.get("task_set_id"),
                "claim_id": claim.get("claim_id"),
                "worktree_path": claim.get("worktree_path"),
                "message": claim.get("status_text"),
                "ts": claim.get("last_heartbeat"),
            },
        )
        receipt["pane_event"] = pane_event
    except Exception as exc:  # noqa: BLE001 - claim authority is committed
        _add_post_commit_warning(
            warnings,
            stage=(
                "claim-heartbeat-event"
                if operation == "heartbeat"
                else "claim-renewal-event"
            ),
            error=exc,
        )
    response = {
        "status": "heartbeated" if operation == "heartbeat" else "renewed",
        "path": _rel(root, path),
        "claim": claim,
        "receipt": receipt,
        "projection": _mutation_projection_payload(root, path, claim),
    }
    if warnings:
        response["status"] = f"{operation}_committed_with_warnings"
        response["post_commit_warnings"] = warnings
    _emit(response, as_json=args.json)
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    try:
        now = _mutation_now(args.now)
        progress = _validate_progress_update(args)
        with claim_store.store_lock(args.root.resolve()):
            outcome = _cmd_claim_mutation_locked(
                args,
                operation="heartbeat",
                now=now,
                progress=progress,
            )
    except (
        AttributeError,
        claim_store.ClaimStoreError,
        OSError,
        OverflowError,
        RuntimeError,
        TimeoutError,
        TypeError,
        ValueError,
    ) as exc:
        detail = " ".join(str(exc).split())[:256] or "claim mutation unavailable"
        print(f"claim heartbeat refused: {detail}", file=sys.stderr)
        return 1
    path, claim, scope_change = outcome
    return _complete_claim_mutation(
        args,
        operation="heartbeat",
        path=path,
        claim=claim,
        scope_change=scope_change,
    )


def cmd_renew(args: argparse.Namespace) -> int:
    try:
        now = _mutation_now(args.now)
        renewal_expires_at = claim_store.expiration_after(
            now,
            args.lease_minutes,
            unit="minutes",
            field="lease_minutes",
            minimum=1,
        )
        with claim_store.store_lock(args.root.resolve()):
            outcome = _cmd_claim_mutation_locked(
                args,
                operation="renew",
                now=now,
                renewal_expires_at=renewal_expires_at,
            )
    except (
        AttributeError,
        claim_store.ClaimStoreError,
        OSError,
        OverflowError,
        RuntimeError,
        TimeoutError,
        TypeError,
        ValueError,
    ) as exc:
        detail = " ".join(str(exc).split())[:256] or "claim mutation unavailable"
        print(f"claim renewal refused: {detail}", file=sys.stderr)
        return 1
    path, claim, scope_change = outcome
    return _complete_claim_mutation(
        args,
        operation="renew",
        path=path,
        claim=claim,
        scope_change=scope_change,
    )


def _normalize_evidence_ref(root: Path, value: str) -> str:
    """Normalize an evidence path into a repo-relative POSIX ref."""
    return _direct_repo_file_ref(root, value, "verification evidence")


def _cross_verification_errors(
    root: Path,
    claim: dict[str, Any],
    *,
    verified_by: str,
    verifier_role: str,
    evidence_ref: str,
    require_evidence: bool,
) -> list[str]:
    """Enforce the cross-verification gate for release (Owner rule:

    작업자 자기검증 금지 — 항상 다른 에이전트가 검증). The W4a worker may run
    verification commands, but only a DIFFERENT agent instance (W4b) can
    approve the release.
    """
    errors: list[str] = []
    worker_id = str(claim.get("agent_instance_id") or "").strip()
    if not verified_by:
        errors.append(
            "cross-verification required: missing --verified-by "
            "(agent_instance_id of the independent W4b verifier); "
            "worker self-verification alone cannot release a claim"
        )
    elif verified_by == worker_id:
        errors.append(
            "cross-verification violation: verifier identity matches worker identity "
            f"(verified_by={verified_by}, worker agent_instance_id={worker_id}); "
            "release requires a different agent instance as verifier"
        )
    if not verifier_role:
        errors.append(
            "cross-verification required: missing --verifier-role (role of the W4b verifier)"
        )
    if require_evidence:
        if not evidence_ref:
            errors.append(
                "verification evidence required: missing --verification-evidence "
                "(repo-relative ref to the W4b verification record); "
                "--allow-missing-evidence is a transitional escape only"
            )
        elif not (root / evidence_ref).exists():
            errors.append(f"verification evidence not found: {evidence_ref}")
    return errors


def cmd_release(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        with claim_store.store_lock(root):
            inspection = claim_store.inspect_store(root)
            if inspection.state not in {"pristine", "initialized"}:
                return _claim_store_refusal("release", inspection)
            outcome = _cmd_release_locked(args, store_inspection=inspection)
    except (
        claim_store.ClaimStoreError,
        TimeoutError,
        OSError,
        RuntimeError,
        ValueError,
    ) as exc:
        detail = " ".join(str(exc).split())[:256] or "claim-store unavailable"
        print(f"claim-store release refused: {detail}", file=sys.stderr)
        return 1
    if isinstance(outcome, int):
        return outcome
    path, claim, verified_by, verifier_role, evidence_ref, now_text = outcome
    return _complete_release(
        args,
        path=path,
        claim=claim,
        verified_by=verified_by,
        verifier_role=verifier_role,
        evidence_ref=evidence_ref,
        now_text=now_text,
    )


def _cmd_release_locked(
    args: argparse.Namespace,
    *,
    store_inspection: Any,
) -> int | tuple[Path, dict[str, Any], str, str, str, str]:
    root = args.root.resolve()
    found = _find_claim(root, args.claim_id)
    if found is None:
        print(f"claim not found: {args.claim_id}", file=sys.stderr)
        return 1

    path, claim = found
    if not _is_active(claim):
        print(
            f"release requires an active claim: {args.claim_id} "
            f"(status={claim.get('status')})",
            file=sys.stderr,
        )
        return 1
    errors: list[str] = []
    pointer_errors: list[str] = []
    for field in ("handoff_path", "log_path"):
        value = claim.get(field)
        if not isinstance(value, str) or not value.strip():
            pointer_errors.append(f"{field} is missing")
            continue
        try:
            _claim_artifact_file_ref(root, value, field)
        except ValueError as exc:
            pointer_errors.append(str(exc))
    if pointer_errors:
        errors.append(f"handoff/log pointer is missing for claim: {args.claim_id}")
        errors.extend(pointer_errors)

    verified_by = str(args.verified_by or "").strip()
    verifier_role = str(args.verifier_role or "").strip()
    try:
        evidence_ref = _normalize_evidence_ref(
            root, args.verification_evidence
        )
    except ValueError as exc:
        evidence_ref = ""
        errors.append(str(exc))
    errors.extend(
        _cross_verification_errors(
            root,
            claim,
            verified_by=verified_by,
            verifier_role=verifier_role,
            evidence_ref=evidence_ref,
            require_evidence=args.require_evidence,
        )
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if not args.require_evidence and not evidence_ref:
        print(
            "WARNING: --allow-missing-evidence used: releasing claim "
            f"{args.claim_id} WITHOUT a verification evidence ref. "
            "This is a transitional escape; attach evidence and backfill "
            "verification_evidence as soon as possible.",
            file=sys.stderr,
        )

    if not claim_store.verify_snapshot(root, store_inspection.snapshot):
        print(
            "claim-store release refused: authority changed before persistence",
            file=sys.stderr,
        )
        return 1

    now_text = _parse_now(args.now).isoformat(timespec="seconds")
    claim["status"] = "released"
    claim["released_at"] = now_text
    claim["last_heartbeat"] = now_text
    claim["updated_at"] = now_text
    claim["verified_by"] = verified_by
    claim["verifier_role"] = verifier_role
    claim["verification_evidence"] = evidence_ref
    lease = claim.get("lease")
    if isinstance(lease, dict):
        lease["heartbeat_at"] = now_text
    atomic_io.write_json_atomic(path, claim)
    return path, claim, verified_by, verifier_role, evidence_ref, now_text


def _complete_release(
    args: argparse.Namespace,
    *,
    path: Path,
    claim: dict[str, Any],
    verified_by: str,
    verifier_role: str,
    evidence_ref: str,
    now_text: str,
) -> int:
    """Run non-authoritative release effects after the store lock is released."""

    root = args.root.resolve()
    post_commit_warnings: list[dict[str, str]] = []
    try:
        append_event(
            root,
            {
                "event": "claim_released",
                "actor": claim.get("agent_instance_id") or "unknown",
                "actor_role": claim.get("agent_role"),
                "agent_instance_id": claim.get("agent_instance_id"),
                "display_name": claim.get("display_name"),
                "callsite_id": claim.get("callsite_id"),
                "task_id": claim.get("task_id"),
                "task_set_id": claim.get("task_set_id"),
                "claim_id": claim.get("claim_id"),
                "worktree_path": claim.get("worktree_path"),
                "verified_by": verified_by,
                "verifier_role": verifier_role,
                "message": (
                    f"Released after cross-verification by {verified_by} "
                    f"({verifier_role})"
                ),
                "ts": now_text,
            },
        )
    except Exception as exc:  # noqa: BLE001 - release authority is already durable
        _add_post_commit_warning(
            post_commit_warnings,
            stage="claim-released-event",
            error=exc,
        )
    # Live A2A traffic: release closes the lifecycle the create-time `request`
    # opened, emitting review -> decision -> correction so the runtime message
    # stream carries a full, reconstructable request->review->decision->correction
    # chain per claim (what a2a_trace_gate validates). Additive observability only;
    # best-effort — the emitter swallows its own errors so release never breaks.
    if a2a_claim_emitter is not None:
        try:
            a2a_claim_emitter.emit_claim_release_chain(
                claim,
                root=root,
                verified_by=verified_by,
                verifier_role=verifier_role,
                verification_evidence=evidence_ref,
            )
        except Exception as exc:  # noqa: BLE001 - additive observability only
            _add_post_commit_warning(
                post_commit_warnings,
                stage="claim-released-a2a",
                error=exc,
            )
    # Dormant-role routing seam (TASK-AR-592): a claim release is a task
    # closeout, a high-risk event the audit flagged as never exercising the
    # review roles. When AR_ROLE_ROUTING is ON, dispatch an ADDITIVE reviewer
    # pass against a DISTINCT synthetic task id; it runs in parallel and never
    # removes or mutates this lead-engineer claim. A HIGH-RISK claim (one
    # carrying escalation_triggers or a risk tag matching an ESCALATION_TRIGGER)
    # ALSO auto-dispatches an adversarial skeptic pass. Flag-OFF (default) and
    # any routing fault are no-ops — a routing failure must NEVER break the
    # release (mirrors the a2a_claim_emitter robustness above).
    try:
        triggers = list(claim.get("escalation_triggers") or []) + [
            t for t in (claim.get("tags") or []) if t in model_routing.ESCALATION_TRIGGERS
        ]
        overlay_marker = claim.get("overlay")
        if isinstance(overlay_marker, str):
            is_overlay = overlay_marker.strip().lower() not in {"", "0", "false", "no", "off", "none", "null"}
        elif overlay_marker is None:
            is_overlay = False
        elif isinstance(overlay_marker, (bool, int, float)):
            is_overlay = bool(overlay_marker)
        else:
            is_overlay = True
        if not is_overlay and role_routing is not None:
            role_routing.route_review_pass(
                root,
                task_id=str(claim.get("task_id") or ""),
                task_set_id=str(claim.get("task_set_id") or ""),
                event="closeout",
                triggers=triggers,
                now=now_text,
            )
    except Exception:  # noqa: BLE001 - routing is best-effort overlay only
        pass
    if str(claim.get("phase") or "").strip().lower() == "taskset-completed":
        # Taskset boundary reached: emit a completion signal so the runtime
        # (boundary guard + UI banner) can enforce STOP-and-report rather than
        # drifting into out-of-scope follow-on work.
        scope = str(claim.get("active_scope") or claim.get("task_set_id") or "").strip()
        try:
            append_event(
                root,
                {
                    "event": "taskset.completed",
                    "actor": claim.get("agent_instance_id") or "unknown",
                    "actor_role": claim.get("agent_role"),
                    "agent_instance_id": claim.get("agent_instance_id"),
                    "display_name": claim.get("display_name"),
                    "callsite_id": claim.get("callsite_id"),
                    "task_id": claim.get("task_id"),
                    "task_set_id": scope,
                    "claim_id": claim.get("claim_id"),
                    "worktree_path": claim.get("worktree_path"),
                    "message": (
                        f"Taskset {scope} completed; stop and report. "
                        "Out-of-scope follow-on work requires owner approval."
                    ),
                    "ts": now_text,
                },
            )
        except Exception as exc:  # noqa: BLE001 - release authority is durable
            _add_post_commit_warning(
                post_commit_warnings,
                stage="taskset-completed-event",
                error=exc,
            )
    response = {"status": "released", "path": _rel(root, path), "claim": claim}
    if post_commit_warnings:
        response["post_commit_warnings"] = post_commit_warnings
    _emit(response, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create/release parallel agent task claims")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a task claim")
    create.add_argument("--task-id", required=True)
    create.add_argument("--agent-role", required=True)
    create.add_argument("--team-id", default="agent-runtime-core")
    create.add_argument("--task-set-id", default="")
    create.add_argument(
        "--active-scope",
        default="",
        help=(
            "Active taskset boundary recorded on the claim (defaults to "
            "--task-set-id). The taskset boundary guard treats work outside "
            "this scope after completion as drift."
        ),
    )
    create.add_argument(
        "--scope-transition-approved",
        action="store_true",
        help=(
            "Mark this claim as an owner-approved scope transition so the "
            "taskset boundary guard does not block it after a prior taskset "
            "completed"
        ),
    )
    create.add_argument("--project-id", default="")
    create.add_argument("--unit-id", default="")
    create.add_argument("--unit-spec", default="")
    create.add_argument(
        "--target-file",
        action="append",
        default=[],
        help="Declared footprint entry, repo-relative (repeatable); derived from --unit-spec when omitted",
    )
    create.add_argument(
        "--model-tier",
        default="",
        help="Requested PM tier; derives from unit/task metadata when omitted",
    )
    create.add_argument(
        "--task-token-budget",
        default="",
        help="Durable cumulative task token budget (explicit -> unit -> task)",
    )
    create.add_argument(
        "--claim-token-budget",
        default="",
        help="Durable cumulative claim token budget (explicit -> unit -> task)",
    )
    create.add_argument("--wip-slot", type=int, default=0)
    create.add_argument("--stop-condition", default="")
    create.add_argument("--mode", default="work")
    create.add_argument("--pane-id")
    create.add_argument("--phase", default="claim-created")
    create.add_argument("--progress-pct", type=int, default=0)
    create.add_argument("--step-index", type=int, default=1)
    create.add_argument("--step-total", type=int, default=6)
    create.add_argument("--status-text", default="Claim created")
    create.add_argument("--tag", action="append", default=[])
    create.add_argument(
        "--defect-signature",
        action="append",
        default=[],
        help="Explicit defect signature or raw stable defect phrase (repeatable)",
    )
    create.add_argument(
        "--escalation-trigger",
        action="append",
        default=[],
        help=(
            "High-risk escalation signal carried on the claim (repeatable), e.g. "
            "high_risk / security / external_effect / cross_cutting / "
            "repeated_failure. Read at closeout to route an adversarial review."
        ),
    )
    create.add_argument("--now")
    create.add_argument("--suffix")
    create.add_argument("--display-name")
    create.add_argument("--agent-instance-id")
    create.add_argument("--callsite-id")
    create.add_argument("--claim-id")
    create.add_argument("--worktree-path")
    create.add_argument("--branch")
    create.add_argument("--handoff-path")
    create.add_argument("--log-path")
    create.add_argument(
        "--lease-minutes",
        type=int,
        default=claim_store.DEFAULT_CLAIM_LEASE_MINUTES,
    )
    create.add_argument("--allow-parallel-task-set", action="store_true")
    create.add_argument(
        "--commit-claim-artifacts",
        action="store_true",
        help=(
            "Explicitly authorize one Git commit containing only the claim "
            "JSON, handoff, and log. Default claim creation never changes HEAD."
        ),
    )
    create.add_argument(
        "--skip-plan-check",
        action="store_true",
        help=(
            "Transitional escape: create the claim even when the taskset's "
            "recorded plan assumptions (T0 snapshot) have drifted; prints a "
            "loud warning instead of refusing (T2 dispatch gate bypass)"
        ),
    )
    create.add_argument("--json", action="store_true")
    create.set_defaults(func=cmd_create)

    heartbeat = sub.add_parser(
        "heartbeat",
        help="Atomically refresh one owned active claim and optional progress",
    )
    heartbeat.add_argument("--claim-id", required=True)
    heartbeat.add_argument("--agent-instance-id", required=True)
    heartbeat.add_argument("--callsite-id", required=True)
    heartbeat.add_argument("--expected-revision", type=int, required=True)
    heartbeat.add_argument("--phase")
    heartbeat.add_argument("--progress-pct", type=int)
    heartbeat.add_argument("--step-index", type=int)
    heartbeat.add_argument("--step-total", type=int)
    heartbeat.add_argument("--status-text")
    heartbeat.add_argument("--now")
    heartbeat.add_argument("--json", action="store_true")
    heartbeat.set_defaults(func=cmd_heartbeat)

    renew = sub.add_parser(
        "renew",
        help="Atomically renew one owned active claim with scope-drift binding",
    )
    renew.add_argument("--claim-id", required=True)
    renew.add_argument("--agent-instance-id", required=True)
    renew.add_argument("--callsite-id", required=True)
    renew.add_argument("--expected-revision", type=int, required=True)
    renew.add_argument("--expected-scope-digest", required=True)
    renew.add_argument("--lease-minutes", type=int, required=True)
    renew.add_argument("--replan-ref", default="")
    renew.add_argument("--now")
    renew.add_argument("--json", action="store_true")
    renew.set_defaults(func=cmd_renew)

    projection = sub.add_parser("projection", help="Emit the required active task/unit/pointer projection for a claim")
    projection.add_argument("--claim-id", required=True)
    projection.add_argument("--now")
    projection.add_argument("--json", action="store_true")
    projection.set_defaults(func=cmd_projection)

    release = sub.add_parser(
        "release",
        help=(
            "Release a task claim after handoff/log files exist and an independent "
            "(W4b) verifier signed off; the verifier must differ from the worker"
        ),
    )
    release.add_argument("--claim-id", required=True)
    release.add_argument(
        "--verified-by",
        default="",
        help=(
            "agent_instance_id of the independent W4b verifier; "
            "must differ from the claim's worker agent_instance_id"
        ),
    )
    release.add_argument(
        "--verifier-role",
        default="",
        help="Role of the independent W4b verifier (e.g. qa-reviewer)",
    )
    release.add_argument(
        "--verification-evidence",
        default="",
        help="Repo-relative path to the W4b verification evidence record",
    )
    release.add_argument(
        "--require-evidence",
        dest="require_evidence",
        action="store_true",
        default=True,
        help="Require a verification evidence ref (default: on)",
    )
    release.add_argument(
        "--allow-missing-evidence",
        dest="require_evidence",
        action="store_false",
        help=(
            "Transitional escape: release without a verification evidence ref; "
            "prints a loud warning and should be backfilled"
        ),
    )
    release.add_argument("--now")
    release.add_argument("--json", action="store_true")
    release.set_defaults(func=cmd_release)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
