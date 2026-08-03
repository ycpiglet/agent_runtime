"""Reconcile live task lifecycle records across claims and projections.

The gate deliberately uses durable lifecycle metadata, not commit-message
guessing.  Its enforcement set is small: active worker claims, pointer-active
work, and verified-but-not-closed work.  Older completed history is therefore
not forced through a migration merely because it pre-dates the claim protocol.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_runtime import claim_store, state_projection


POINTER = Path("agents/project/NEXT-SESSION-POINTER.yml")
TASKS_DIR = Path("agents/lead_engineer/tasks")
CLAIMS_DIR = Path("agents/runtime/task_claims")
BOARD = Path("BACKLOG-BOARD.md")
BACKLOG = Path("BACKLOG.md")
STATUS = Path("STATUS.md")
try:
    import status_alias
except ImportError:  # imported as scripts.<name> (namespace package)
    from scripts import status_alias
DONE_STATUSES = status_alias.DONE_STATUSES
# Canonical set, imported rather than re-typed: "every surface agrees on
# active versus expired" must hold by construction, not by coincidence.
ACTIVE_CLAIM_STATUSES = claim_store.ACTIVE_CLAIM_STATUSES
STATE_PROJECTION_BLOCKING_CODES = {
    "config-invalid",
    "source-missing",
    "source-unsafe",
    "source-parse-error",
    "source-too-large",
    "projection-missing",
    "projection-stale",
    "projection-unsafe",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    subject: str
    path: str
    detail: str


def _parse_aware_datetime(value: str) -> datetime:
    raw = value.strip()
    normalized = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "invalid --now: expected a timezone-aware ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError(
            "invalid --now: expected a timezone-aware ISO-8601 timestamp"
        )
    return parsed


@dataclass(frozen=True)
class WorkItem:
    work_id: str
    path: Path
    meta: dict[str, object]

    @property
    def status(self) -> str:
        value = self.meta.get("status")
        return status_alias.normalize_status(value) if isinstance(value, str) and value.strip() else "unknown"

    @property
    def task_set_id(self) -> str:
        return str(self.meta.get("task_set_id") or "").strip()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*['\"]?([^'\"\n#]+)", text)
    return match.group(1).strip() if match else ""


def _frontmatter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, object] = {}
    current_key = ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        item = re.match(r"^\s*-\s+(.*?)\s*$", line)
        if item and current_key:
            current = out.setdefault(current_key, [])
            if isinstance(current, list):
                current.append(item.group(1).strip().strip("'\""))
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if not match:
            current_key = ""
            continue
        key, value = match.groups()
        if value:
            out[key] = value.strip().strip("'\"")
            current_key = ""
        else:
            out[key] = []
            current_key = key
    return out


def _values(meta: dict[str, object], key: str) -> list[str]:
    value = meta.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def load_tasks(root: Path) -> list[WorkItem]:
    task_dir = root / TASKS_DIR
    if not task_dir.is_dir():
        return []
    tasks: list[WorkItem] = []
    for path in sorted(task_dir.glob("TASK-*.md")):
        meta = _frontmatter(_read(path))
        tasks.append(WorkItem(str(meta.get("id") or meta.get("work_id") or path.stem), path, meta))
    return tasks


def load_units(root: Path) -> list[WorkItem]:
    unit_dir = root / TASKS_DIR / "units"
    if not unit_dir.is_dir():
        return []
    units: list[WorkItem] = []
    for path in sorted(unit_dir.glob("**/UNIT-*.md")):
        meta = _frontmatter(_read(path))
        units.append(WorkItem(str(meta.get("unit_id") or meta.get("work_id") or path.stem), path, meta))
    return units


def _pointer_block(text: str, label: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^(?P<indent>\s*){re.escape(label)}:\s*$", line)
        if not match:
            continue
        indent = len(match.group("indent"))
        body: list[str] = []
        for child in lines[index + 1 :]:
            if child.strip() and len(child) - len(child.lstrip()) <= indent:
                break
            body.append(child)
        return body
    return []


def _pointer_list(text: str, label: str) -> list[str]:
    return [match.group(1).strip().strip("'\"") for line in _pointer_block(text, label) if (match := re.match(r"^\s*-\s+(.*?)\s*$", line))]


def _pointer_agents(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in _pointer_block(text, "current_agents"):
        item = re.match(r"^\s*-\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        field = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if item:
            current = {item.group(1): item.group(2).strip().strip("'\"")}
            records.append(current)
        elif field and current is not None:
            current[field.group(1)] = field.group(2).strip().strip("'\"")
    return records


def active_pointer(root: Path) -> tuple[str, str, str]:
    text = _read(root / POINTER)
    return (
        _scalar(text, "active_task_set") or _scalar(text, "task_set_id"),
        _scalar(text, "active_task"),
        _scalar(text, "status"),
    )


def _contains(root: Path, path: Path, needle: str) -> bool:
    return not needle or needle == "none" or needle in _read(root / path)


def _configured_state_contract(root: Path) -> tuple[bool, list[Finding]]:
    """Validate explicit v2 state adapters without asserting on host content.

    Legacy and unconfigured hosts retain the historical BACKLOG/STATUS checks.
    Once a host explicitly configures an adapter, its source stays read-only and
    the generated, digest-pinned projection becomes the Runtime-facing contract.
    """

    try:
        settings = state_projection.resolve_settings(root)
    except Exception as exc:
        return True, [
            Finding(
                "block",
                "state-projection:evaluation-error",
                "agent_runtime.yml",
                f"state adapter settings could not be resolved: {exc}",
            )
        ]
    setting_codes = {
        str(finding.get("code") or "")
        for finding in settings.findings
        if isinstance(finding, dict)
    }
    configured = any(source.configured for source in settings.sources)
    configured = configured or "config-invalid" in setting_codes
    if not configured:
        return False, []

    try:
        evaluation = state_projection.evaluate_state(root)
    except Exception as exc:
        return True, [
            Finding(
                "block",
                "state-projection:evaluation-error",
                settings.projection_path,
                f"configured state projection could not be evaluated: {exc}",
            )
        ]

    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for raw in evaluation.get("findings", []):
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("code") or "")
        if code not in STATE_PROJECTION_BLOCKING_CODES:
            continue
        path = str(raw.get("path") or settings.projection_path)
        key = (code, path)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            Finding(
                "block",
                f"state-projection:{code}",
                path,
                str(raw.get("detail") or "configured state projection is invalid"),
            )
        )
    projection_status = str(
        (evaluation.get("projection") or {}).get("status") or ""
    )
    if projection_status != "fresh" and not any(
        finding.subject
        in {
            "state-projection:projection-missing",
            "state-projection:projection-stale",
            "state-projection:projection-unsafe",
        }
        for finding in findings
    ):
        findings.append(
            Finding(
                "block",
                f"state-projection:projection-{projection_status or 'invalid'}",
                settings.projection_path,
                "configured state adapters require a fresh generated projection",
            )
        )
    return True, findings


def _is_active(claim: dict[str, object]) -> bool:
    return str(claim.get("status") or "").strip().lower() in ACTIVE_CLAIM_STATUSES


def _is_explicit_overlay(claim: dict[str, object]) -> bool:
    """Only an affirmative, well-formed overlay marker earns the exemption."""
    return claim.get("overlay") is True


def _claim_records(root: Path) -> tuple[list[tuple[Path, dict[str, object]]], list[Finding]]:
    records: list[tuple[Path, dict[str, object]]] = []
    findings: list[Finding] = []
    for path in sorted((root / CLAIMS_DIR).glob("*.json")) if (root / CLAIMS_DIR).is_dir() else []:
        try:
            claim = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            findings.append(Finding("block", f"claim:malformed:{path.name}", _rel(root, path), "claim is not valid JSON"))
            continue
        if not isinstance(claim, dict):
            findings.append(Finding("block", f"claim:malformed:{path.name}", _rel(root, path), "claim must be a JSON object"))
            continue
        records.append((path, claim))
    return records, findings


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _worktree(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    root_candidate = root / path
    if root_candidate.exists():
        return root_candidate
    primary_root = _git_primary_root(root)
    if primary_root is not None and primary_root != root:
        primary_candidate = primary_root / path
        if primary_candidate.exists():
            return primary_candidate
    return root_candidate


def _git_primary_root(root: Path) -> Path | None:
    """Return the Git common-dir parent, without guessing when Git is absent."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = root / common
    try:
        return common.resolve().parent
    except OSError:
        return common.absolute().parent


def _branch_matches_worktree(worktree: Path, branch: str) -> bool:
    """Confirm the claimed branch is checked out by its claimed worktree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(worktree), "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == branch


def _is_main_checkout(worktree: Path) -> bool:
    """Return true only when Git proves this path is its common-dir parent."""
    primary_root = _git_primary_root(worktree)
    return primary_root is not None and worktree.resolve() == primary_root.resolve()


def _recovery_errors(root: Path, item: WorkItem) -> list[str]:
    required = ("recovery_reason", "recovered_at", "recovered_by")
    errors = [field for field in required if not str(item.meta.get(field) or "").strip()]
    refs = _values(item.meta, "recovery_independent_evidence_refs")
    if not refs:
        errors.append("recovery_independent_evidence_refs")
    else:
        errors.extend(f"recovery_evidence_missing:{ref}" for ref in refs if not (root / ref).is_file())
    return errors


def _has_recovery(item: WorkItem) -> bool:
    return str(item.meta.get("recovered_without_claim") or "").strip().lower() == "true"


def _claim_for_item(records: list[tuple[Path, dict[str, object]]], task_id: str, unit_id: str) -> bool:
    return any(
        not _is_explicit_overlay(claim)
        and str(claim.get("task_id") or "") == task_id
        and str(claim.get("unit_id") or "") == unit_id
        for _, claim in records
    )


def _validate_active_claim(
    root: Path,
    claim_path: Path,
    claim: dict[str, object],
    tasks: dict[str, WorkItem],
    units: dict[str, WorkItem],
    pointer_taskset: str,
    pointer_task: str,
    pointer_claim_refs: list[str],
    pointer_agents: list[dict[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    claim_id = str(claim.get("claim_id") or claim_path.stem)
    rel_claim_path = _rel(root, claim_path)
    overlay = _is_explicit_overlay(claim)
    if overlay:
        for field in ("claim_id", "task_id", "task_set_id", "agent_role", "agent_instance_id"):
            if not str(claim.get(field) or "").strip():
                findings.append(Finding("block", f"claim:missing-overlay-field:{claim_id}:{field}", rel_claim_path, "explicit overlay lacks minimal identity/provenance metadata"))
        # Overlays intentionally model review/scout traffic that may not map to
        # worker task, unit, branch, worktree, or pointer projections.
        return findings
    required = ("task_id", "task_set_id", "unit_id", "agent_role", "agent_instance_id")
    required += ("worktree_path", "branch")
    for field in required:
        if not str(claim.get(field) or "").strip():
            findings.append(Finding("block", f"claim:missing-worker-field:{claim_id}:{field}", rel_claim_path, "active worker claim lacks required lifecycle metadata"))
    task_id, unit_id = str(claim.get("task_id") or ""), str(claim.get("unit_id") or "")
    task, unit = tasks.get(task_id), units.get(unit_id)
    if task is None:
        findings.append(Finding("block", f"claim:task-missing:{claim_id}", rel_claim_path, f"task {task_id or 'missing'} is not canonical"))
    if unit is None or str(unit.meta.get("task_id") or unit.meta.get("parent_id") or "") != task_id:
        findings.append(Finding("block", f"claim:unit-mismatch:{claim_id}", rel_claim_path, "claim unit is missing or belongs to another task"))
    if task and str(claim.get("task_set_id") or "") != task.task_set_id:
        findings.append(Finding("block", f"claim:taskset-mismatch:{claim_id}", rel_claim_path, "claim and task taskset differ"))
    if unit and (
        unit.task_set_id != str(claim.get("task_set_id") or "")
        or (task is not None and unit.task_set_id != task.task_set_id)
    ):
        findings.append(Finding("block", f"claim:unit-taskset-mismatch:{claim_id}", unit.path.as_posix(), "unit, task, and claim taskset identifiers must agree"))
    allowed_lifecycle_statuses = {"active", "in_progress", "blocked", "review"}
    for item, label in ((task, "task"), (unit, "unit")):
        if item and item.status not in allowed_lifecycle_statuses:
            findings.append(
                Finding(
                    "block",
                    f"claim:{label}-invalid-lifecycle:{claim_id}:{item.status or 'missing'}",
                    item.path.as_posix(),
                    "active worker claim requires canonical work projected to active/in_progress/blocked/review",
                )
            )
    for item, label in ((task, "task"), (unit, "unit")):
        if item and rel_claim_path not in _values(item.meta, "claim_refs"):
            findings.append(Finding("block", f"claim:missing-{label}-ref:{claim_id}", item.path.as_posix(), "claim path is not projected in claim_refs"))
    worktree_value = str(claim.get("worktree_path") or "").strip()
    if worktree_value:
        worktree = _worktree(root, worktree_value)
        if _is_main_checkout(worktree):
            findings.append(Finding("block", f"claim:main-worktree:{claim_id}", rel_claim_path, "worker claim must not use the main checkout"))
        elif not worktree.is_dir() or not (worktree / ".git").exists():
            findings.append(Finding("block", f"claim:invalid-worktree:{claim_id}", rel_claim_path, "worker worktree is absent or not a git worktree"))
        elif not _branch_matches_worktree(worktree, str(claim.get("branch") or "")):
            findings.append(Finding("block", f"claim:branch-mismatch:{claim_id}", rel_claim_path, "claimed branch is not checked out by claimed worktree"))
    if rel_claim_path not in pointer_claim_refs:
        findings.append(Finding("block", f"claim:pointer-missing-active-ref:{claim_id}", POINTER.as_posix(), "claim is absent from pointers.active_claims"))
    agent = next((entry for entry in pointer_agents if entry.get("claim_id") == claim_id), None)
    if agent is None:
        findings.append(Finding("block", f"claim:pointer-missing-agent:{claim_id}", POINTER.as_posix(), "current_agents lacks a full record keyed by claim_id"))
    else:
        for field in ("agent_role", "agent_instance_id"):
            if agent.get(field) != str(claim.get(field) or ""):
                findings.append(Finding("block", f"claim:pointer-agent-mismatch:{claim_id}:{field}", POINTER.as_posix(), "current_agents identity differs from claim"))
    return findings


def analyze(
    root: Path,
    *,
    now: datetime | None = None,
    grace_seconds: object | None = None,
) -> list[Finding]:
    root = root.resolve()
    now_dt = now or datetime.now(timezone.utc)
    grace = claim_store.resolve_claim_grace(grace_seconds)
    pointer_path = root / POINTER
    if not pointer_path.exists():
        return [Finding("block", "pointer:missing", POINTER.as_posix(), "NEXT-SESSION-POINTER.yml is required")]
    findings: list[Finding] = []
    pointer_text = _read(pointer_path)
    task_set_id, active_task, pointer_status = active_pointer(root)
    tasks = load_tasks(root)
    units = load_units(root)
    by_id = {task.work_id: task for task in tasks}
    units_by_id = {unit.work_id: unit for unit in units}
    taskset_tasks = [task for task in tasks if task.task_set_id == task_set_id]

    if not task_set_id or task_set_id == "none":
        findings.append(Finding("watch", "pointer:no-active-taskset", POINTER.as_posix(), "pointer has no active taskset"))
    elif not taskset_tasks:
        findings.append(Finding("block", f"taskset:missing:{task_set_id}", TASKS_DIR.as_posix(), "active taskset has no canonical task files"))
    if active_task and active_task != "none":
        task = by_id.get(active_task)
        if task is None:
            findings.append(Finding("block", f"active-task:missing:{active_task}", POINTER.as_posix(), "active task is not present in task files"))
        elif task.task_set_id != task_set_id:
            findings.append(Finding("block", f"active-task:taskset-mismatch:{active_task}", task.path.as_posix(), f"active task belongs to {task.task_set_id}, pointer says {task_set_id}"))
        elif task.status in status_alias.DONE_CANONICAL:
            findings.append(Finding("block", f"active-task:done:{active_task}", task.path.as_posix(), "pointer cannot select a completed task as active"))
    open_tasks = [task for task in taskset_tasks if task.status not in DONE_STATUSES]
    taskset_is_complete = bool(taskset_tasks) and not open_tasks
    if task_set_id and task_set_id != "none" and pointer_status in {"active", "in_progress"} and taskset_tasks and not open_tasks:
        findings.append(Finding("block", f"taskset:active-but-complete:{task_set_id}", POINTER.as_posix(), "pointer says active but all taskset tasks are done"))
    configured_state, configured_state_findings = _configured_state_contract(root)
    findings.extend(configured_state_findings)
    state_surfaces = (BOARD,) if configured_state else (BOARD, BACKLOG, STATUS)
    for path in state_surfaces:
        if not (root / path).exists():
            findings.append(Finding("block", f"surface:missing:{path.as_posix()}", path.as_posix(), "required state surface is missing"))
        elif task_set_id and task_set_id != "none" and not (path == BOARD and taskset_is_complete and pointer_status not in {"active", "in_progress"}) and not _contains(root, path, task_set_id):
            findings.append(Finding("block", f"surface:missing-taskset:{path.as_posix()}", path.as_posix(), f"{path.as_posix()} does not mention active taskset {task_set_id}"))
    if active_task and active_task != "none":
        active_task_surfaces = (BOARD,) if configured_state else (BOARD, STATUS)
        for path in active_task_surfaces:
            if (root / path).exists() and not _contains(root, path, active_task):
                findings.append(Finding("watch", f"surface:missing-active-task:{path.as_posix()}", path.as_posix(), f"{path.as_posix()} does not mention active task {active_task}"))

    records, claim_findings = _claim_records(root)
    findings.extend(claim_findings)
    pointer_claim_refs = _pointer_list(pointer_text, "active_claims")
    pointer_agents = _pointer_agents(pointer_text)
    classified = [
        (
            claim_path,
            claim,
            claim_store.classify_claim_liveness(
                claim,
                now=now_dt,
                grace_seconds=grace,
            ),
        )
        for claim_path, claim in records
    ]
    for claim_path, claim, liveness in classified:
        claim_id = str(claim.get("claim_id") or claim_path.stem)
        rel_claim_path = _rel(root, claim_path)
        if liveness.state == "expired":
            findings.append(
                Finding(
                    "block",
                    f"claim:liveness-expired:{claim_id}",
                    rel_claim_path,
                    "status-active claim authority expired beyond shared grace",
                )
            )
        elif liveness.state == "indeterminate":
            findings.append(
                Finding(
                    "block",
                    f"claim:liveness-indeterminate:{claim_id}",
                    rel_claim_path,
                    f"claim authority is retained conservatively: {liveness.reason}",
                )
            )
        if any("mismatch" in item for item in liveness.findings):
            findings.append(
                Finding(
                    "watch",
                    f"claim:liveness-deadline-mismatch:{claim_id}",
                    rel_claim_path,
                    "top-level and nested claim deadlines differ; later valid deadline is effective",
                )
            )

    authority_records = [
        (claim_path, claim)
        for claim_path, claim, liveness in classified
        if liveness.state in {"live", "indeterminate"}
    ]
    for claim_path, claim in authority_records:
        findings.extend(
            _validate_active_claim(
                root,
                claim_path,
                claim,
                by_id,
                units_by_id,
                task_set_id,
                active_task,
                pointer_claim_refs,
                pointer_agents,
            )
        )
    active_workers = [
        claim
        for _, claim in authority_records
        if not _is_explicit_overlay(claim)
    ]
    if active_workers:
        if not task_set_id or task_set_id == "none":
            findings.append(Finding("block", "pointer:primary-worker-missing-taskset", POINTER.as_posix(), "active worker claims require a primary pointer taskset"))
        elif not active_task or active_task == "none":
            findings.append(Finding("block", "pointer:primary-worker-missing-task", POINTER.as_posix(), "active worker claims require a primary pointer task"))
        elif not any(
            str(claim.get("task_id") or "") == active_task and str(claim.get("task_set_id") or "") == task_set_id
            for claim in active_workers
        ):
            findings.append(Finding("block", f"pointer:primary-worker-missing:{active_task}", POINTER.as_posix(), "primary pointer task/taskset does not correspond to any active worker claim"))

    # Verified, still-current units must have a durable claim trace or an explicit
    # recovery. This catches the TASK-AR-631 shape without migrating closed legacy work.
    for unit in units:
        task_id = str(unit.meta.get("task_id") or unit.meta.get("parent_id") or "")
        task = by_id.get(task_id)
        if (
            not task
            or task.status in DONE_STATUSES
            or str(task.meta.get("verification_status") or "").strip().lower() != "passed"
            or str(unit.meta.get("verification_status") or "").strip().lower() != "passed"
        ):
            continue
        if _has_recovery(task) and _has_recovery(unit):
            errors = _recovery_errors(root, task) + _recovery_errors(root, unit)
            if errors:
                findings.append(Finding("block", f"recovery:invalid:{task_id}", task.path.as_posix(), ", ".join(errors)))
            else:
                findings.append(Finding("watch", f"recovery:without-claim:{task_id}", task.path.as_posix(), "historical missing claim is explicitly recovered from independent evidence"))
        elif not _claim_for_item(records, task_id, unit.work_id):
            findings.append(Finding("block", f"verified-work:missing-lifecycle:{task_id}", unit.path.as_posix(), "verified current work has neither a claim nor explicit recovery"))
    return findings


def render(root: Path, findings: list[Finding]) -> str:
    counts = Counter(f.severity for f in findings)
    status = "fail" if counts.get("block", 0) else "pass"
    lines = [f"state-sync-gate: {status}", f"root={root.resolve()}", f"findings={len(findings)}", f"block={counts.get('block', 0)}", f"watch={counts.get('watch', 0)}"]
    lines.extend(f"- {f.severity} {f.subject} {f.path}: {f.detail}" for f in findings)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Active state sync gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail on block findings")
    parser.add_argument(
        "--now",
        type=_parse_aware_datetime,
        help="Evaluate claim liveness at a timezone-aware ISO-8601 timestamp",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = analyze(args.root, now=args.now)
    print(render(args.root, findings))
    return 1 if args.check and any(f.severity == "block" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
