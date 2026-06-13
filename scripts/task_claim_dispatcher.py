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

Create runs the deferred plan revalidation check (T2, TASK-AR-506) by default:
when the claim's task_set_id has a recorded assumption set in
agents/project/work-items/PLAN-ASSUMPTIONS.json, drifted anchors refuse claim
creation until a replan review re-records them (--skip-plan-check is a loud
transitional escape). This makes the W0~W6 lifecycle the default for all work,
not an opt-in per taskset.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import backlog_board
import plan_assumption_gate
from agent_instance_registry import record_claim_instance
from footprint_conflict_gate import ACTIVE_CLAIM_STATUSES as FOOTPRINT_ACTIVE_STATUSES
from footprint_conflict_gate import footprints_overlap
from pane_event_log import append_event


SCHEMA = "agent-runtime-task-claim/v1"
ACTIVE_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}
ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}


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


def _claim_files(root: Path) -> list[Path]:
    base = _claim_dir(root)
    if not base.is_dir():
        return []
    return sorted(base.glob("*.json"), key=lambda path: path.name.lower())


def _read_claim(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _read_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in _claim_files(root):
        payload = _read_claim(path)
        if payload is not None:
            records.append((path, payload))
    return records


def _is_active(payload: dict[str, Any]) -> bool:
    return str(payload.get("status") or "").strip().lower() in ACTIVE_STATUSES


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
            if worktree == root.resolve():
                errors.append("task worktree is not ready: worker claims must not point at the main checkout")
            elif not worktree.is_dir():
                errors.append(
                    f"task worktree is not ready: {worktree_value} does not exist; "
                    f"run: git worktree add -b {claim.get('branch')} {worktree_value}"
                )
            elif not _has_git_worktree_marker(worktree):
                errors.append(f"task worktree is not ready: {worktree_value} is not a git worktree")

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
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _resolve_target_files(root: Path, args: argparse.Namespace) -> list[str]:
    declared = [str(entry).strip() for entry in (args.target_file or []) if str(entry).strip()]
    if declared:
        return declared
    return _unit_spec_target_files(root, args.unit_spec)


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


def _ensure_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(text, encoding="utf-8")


def _build_claim(
    args: argparse.Namespace,
    records: list[tuple[Path, dict[str, Any]]],
    *,
    target_files: list[str],
) -> dict[str, Any]:
    now = _parse_now(args.now)
    expires_at = now + timedelta(minutes=args.lease_minutes)
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
        "project_id": args.project_id,
        "unit_id": args.unit_id,
        "unit_spec": args.unit_spec,
        "model_tier": args.model_tier,
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
        "target_files": list(target_files),
    }


def _validate_create_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
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


def _plan_assumption_findings(root: Path, task_set_id: str) -> list[str] | None:
    """Return T2 drift findings for the taskset's recorded assumption set.

    ``None`` means no snapshot is recorded for this taskset (T0 never ran);
    an empty list means the snapshot exists and every anchor still holds.
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


def _plan_check_refusal(root: Path, task_set_id: str, *, skip_plan_check: bool) -> bool:
    """T2 dispatch gate: verify the taskset's recorded plan assumptions.

    Returns True when claim creation must be refused. All output goes to
    stderr so --json stdout stays machine-readable.
    """
    try:
        findings = _plan_assumption_findings(root, task_set_id)
    except (OSError, ValueError) as exc:
        findings = [f"registry-unreadable:{plan_assumption_gate.REGISTRY_REL}:{exc}"]
    if findings is None:
        print(
            f"note: no plan-assumption snapshot recorded for {task_set_id} "
            "(T0 skipped at registration); T2 drift check has nothing to verify. "
            "Record one with: python scripts/plan_assumption_gate.py record "
            f"--taskset {task_set_id} --design-record <review> --anchor <path>",
            file=sys.stderr,
        )
        return False
    if not findings:
        print(f"plan-assumption-gate: pass ({task_set_id})", file=sys.stderr)
        return False
    if skip_plan_check:
        print(
            "WARNING: --skip-plan-check used: creating claim for "
            f"{task_set_id} DESPITE drifted plan assumptions (T2 dispatch gate bypassed):",
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
    print(
        f"plan assumption drift detected for {task_set_id}: "
        "claim creation refused (T2 dispatch gate)",
        file=sys.stderr,
    )
    for finding in findings:
        print(f"- {finding}", file=sys.stderr)
    print(
        "action=drifted plan assumptions; run a replan review for the affected "
        "taskset, then re-record anchors (python scripts/plan_assumption_gate.py "
        f"record --taskset {task_set_id} --design-record <review> --anchor <path>) "
        "before dispatch. --skip-plan-check is a loud transitional escape only.",
        file=sys.stderr,
    )
    return True


def cmd_create(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    errors = _validate_create_args(args)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    records = _read_claims(root)
    for path, payload in records:
        if not _is_active(payload):
            continue
        if str(payload.get("task_id") or "") == args.task_id:
            print(
                f"task already has an active claim: {args.task_id} ({_rel(root, path)})",
                file=sys.stderr,
            )
            return 1

    task_set_id = str(args.task_set_id or "").strip()
    if task_set_id and _plan_check_refusal(
        root, task_set_id, skip_plan_check=args.skip_plan_check
    ):
        return 1

    claim = _build_claim(args, records, target_files=_resolve_target_files(root, args))
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
    claim_dir = _claim_dir(root)
    claim_dir.mkdir(parents=True, exist_ok=True)
    claim_path = claim_dir / f"{claim['claim_id']}.json"
    if claim_path.exists():
        print(f"claim file already exists: {_rel(root, claim_path)}", file=sys.stderr)
        return 1

    _ensure_text_file(
        root / str(claim["handoff_path"]),
        "\n".join(
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
                f"- model_tier: {claim['model_tier']}",
                f"- wip_slot: {claim['wip_slot']}",
                f"- stop_condition: {claim['stop_condition']}",
                f"- phase: {claim['phase']}",
                f"- step: {claim['step_index']}/{claim['step_total']}",
                f"- progress_pct: {claim['progress_pct']}",
                f"- status_text: {claim['status_text']}",
                "- status: claimed",
                "",
            ]
        ),
    )
    _ensure_text_file(
        root / str(claim["log_path"]),
        "\n".join(
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
                f"- model_tier: {claim['model_tier']}",
                f"- wip_slot: {claim['wip_slot']}",
                f"- stop_condition: {claim['stop_condition']}",
                f"- status_text: {claim['status_text']}",
                "",
            ]
        ),
    )

    claim_path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    record_claim_instance(root, claim, claim_path=claim_path)
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
    _emit({"status": "created", "path": _rel(root, claim_path), "claim": claim}, as_json=args.json)
    return 0


def _find_claim(root: Path, claim_id: str) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in _read_claims(root):
        if str(payload.get("claim_id") or "") == claim_id:
            return path, payload
    return None


def _normalize_evidence_ref(root: Path, value: str) -> str:
    """Normalize an evidence path into a repo-relative POSIX ref."""
    text = str(value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute():
        return _rel(root, path)
    return path.as_posix()


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
    found = _find_claim(root, args.claim_id)
    if found is None:
        print(f"claim not found: {args.claim_id}", file=sys.stderr)
        return 1

    path, claim = found
    errors: list[str] = []
    missing = [
        str(claim.get(field) or "")
        for field in ("handoff_path", "log_path")
        if not str(claim.get(field) or "").strip() or not (root / str(claim.get(field))).exists()
    ]
    if missing:
        errors.append(f"handoff/log pointer is missing for claim: {args.claim_id}")

    verified_by = str(args.verified_by or "").strip()
    verifier_role = str(args.verifier_role or "").strip()
    evidence_ref = _normalize_evidence_ref(root, args.verification_evidence)
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
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
            "message": f"Released after cross-verification by {verified_by} ({verifier_role})",
            "ts": now_text,
        },
    )
    _emit({"status": "released", "path": _rel(root, path), "claim": claim}, as_json=args.json)
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
    create.add_argument("--project-id", default="")
    create.add_argument("--unit-id", default="")
    create.add_argument("--unit-spec", default="")
    create.add_argument(
        "--target-file",
        action="append",
        default=[],
        help="Declared footprint entry, repo-relative (repeatable); derived from --unit-spec when omitted",
    )
    create.add_argument("--model-tier", default="")
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
    create.add_argument("--lease-minutes", type=int, default=30)
    create.add_argument("--allow-parallel-task-set", action="store_true")
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
