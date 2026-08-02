"""Closure gate — require compound/review/retro records for substantial work.

Stop-hook gate (TASK-AR-556 / RETRO-2026-06-14 forward action #6). When the recent
session made *substantial* code changes but recorded no closure — a COMPOUND entry,
a reviews/REVIEW-<date>-*-closeout, or a reviews/RETRO-<date>-* — the Stop hook
blocks closure with guidance, so compound/review/retro is not silently skipped.
Trivial work is exempt (a line-churn threshold), and the gate is best-effort and
escapable.

Environment:
  AGENT_RUNTIME_CLOSURE_GATE_DISABLE=1      bypass (approve)
  AGENT_RUNTIME_CLOSURE_GATE_THRESHOLD=N    substantial-line threshold (default 80)
  AGENT_RUNTIME_CLOSURE_GATE_WINDOW_HOURS=H git look-back window (default 12)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_runtime import state_projection

try:
    import backlog_board
    import compound_record
except ImportError:  # imported as scripts.<name>
    from scripts import backlog_board, compound_record

DEFAULT_THRESHOLD = 80
DEFAULT_WINDOW_HOURS = 12
CODE_PATHS = ("src", "scripts", "tests")
RECORD_KINDS = ("compound", "review", "retro")
ACTIVE_CLAIM_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}
CLAIM_AUTHORITY_FIELDS = (
    "escalation_triggers",
    "defect_signatures",
    "compound_refs",
)
_WINDOWS_REPARSE_POINT_ATTRIBUTE = getattr(
    stat,
    "FILE_ATTRIBUTE_REPARSE_POINT",
    0x0400,
)
_WINDOWS_NAME_SURROGATE_TAG = 0x20000000


def _parse_now(value: str | None = None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _coerce_now(value: str | datetime | None) -> datetime:
    return value if isinstance(value, datetime) else _parse_now(value)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() not in ("0", "false", "no", "off")


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""
    return result.stdout if result.returncode == 0 else ""


def _git_primary_root(root: Path) -> Path | None:
    """Return the primary checkout for the repository containing ``root``."""

    common_text = _git(root, "rev-parse", "--git-common-dir").strip()
    if not common_text:
        return None
    common = Path(common_text)
    if not common.is_absolute():
        common = root / common
    try:
        return common.resolve().parent
    except OSError:
        return common.absolute().parent


def _resolved_claim_worktree(
    root: Path,
    value: str,
    *,
    primary_root: Path | None,
) -> Path | None:
    """Resolve protocol-relative claim paths against the primary checkout."""

    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        candidates = [path]
    elif (
        primary_root is not None
        and primary_root.resolve() != root.resolve()
    ):
        # Protocol-relative paths are anchored only at the primary checkout.
        # Falling back to the linked root lets a shadow path become authority
        # whenever the canonical primary-relative target is absent.
        candidates = [primary_root / path]
    else:
        candidates = [root / path]
    resolved: list[Path] = []
    for candidate in candidates:
        try:
            resolved.append(candidate.resolve())
        except OSError:
            resolved.append(candidate.absolute())
    for candidate in resolved:
        if candidate.exists():
            return candidate
    return resolved[0] if resolved else None


def _sum_numstat(text: str) -> int:
    total = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        added, deleted = parts[0], parts[1]
        for value in (added, deleted):
            if value.isdigit():
                total += int(value)
    return total


def count_substantial_lines(
    root: Path,
    *,
    now: str | datetime | None = None,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    code_paths: tuple[str, ...] = CODE_PATHS,
) -> int:
    """Total added+deleted lines across code paths in the window (committed +
    uncommitted). Best-effort: any git failure contributes 0."""
    moment = _coerce_now(now)
    since = (moment - timedelta(hours=window_hours)).isoformat()
    paths = list(code_paths)
    total = _sum_numstat(_git(root, "log", f"--since={since}", "--numstat", "--pretty=format:", "--", *paths))
    total += _sum_numstat(_git(root, "diff", "--numstat", "--", *paths))
    total += _sum_numstat(_git(root, "diff", "--cached", "--numstat", "--", *paths))
    # Untracked code files are absent from `git diff`; count their lines directly.
    for rel in _git(root, "ls-files", "--others", "--exclude-standard", "--", *paths).splitlines():
        rel = rel.strip()
        if not rel:
            continue
        try:
            with (Path(root) / rel).open(encoding="utf-8", errors="replace") as handle:
                total += sum(1 for _ in handle)
        except OSError:
            continue
    return total


def _list_value(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _work_item_path(root: Path, work_id: str) -> Path | None:
    candidates: list[Path] = []
    if work_id.startswith("UNIT-"):
        task_id = work_id.removeprefix("UNIT-").rsplit("-", 1)[0]
        candidates.append(
            root
            / "agents"
            / "lead_engineer"
            / "tasks"
            / "units"
            / task_id
            / f"{work_id}.md"
        )
    candidates.append(
        root / "agents" / "lead_engineer" / "tasks" / f"{work_id}.md"
    )
    for path in candidates:
        if path.is_file():
            return path
    tasks = root / "agents" / "lead_engineer" / "tasks"
    for path in sorted(tasks.glob(f"**/{work_id}.md")) if tasks.is_dir() else []:
        if path.is_file():
            return path
    return None


def _read_work(path: Path) -> dict[str, Any] | None:
    try:
        meta, _body = backlog_board.parse_frontmatter(
            path.read_text(encoding="utf-8")
        )
    except OSError:
        return None
    return dict(meta) if meta else None


def _claim_is_overlay(claim: dict[str, Any]) -> bool:
    marker = claim.get("overlay")
    if isinstance(marker, str):
        return marker.strip().lower() not in {
            "",
            "0",
            "false",
            "no",
            "off",
            "none",
            "null",
        }
    if marker is None:
        return False
    if isinstance(marker, (bool, int, float)):
        return bool(marker)
    return True


def _claim_authority_shape_valid(claim: dict[str, Any]) -> bool:
    for field in CLAIM_AUTHORITY_FIELDS:
        if field not in claim:
            continue
        value = claim[field]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            return False
    return True


def _claim_store_component_is_alias(metadata: Any) -> bool:
    """Reject path aliases and uninspectable Windows reparse metadata."""

    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_tag = getattr(metadata, "st_reparse_tag", None)
    if isinstance(reparse_tag, int) and (
        reparse_tag & _WINDOWS_NAME_SURROGATE_TAG
    ):
        return True
    if not isinstance(attributes, int):
        return True
    if not attributes & _WINDOWS_REPARSE_POINT_ATTRIBUTE:
        return False
    return not isinstance(reparse_tag, int) or reparse_tag == 0


def _active_claims(
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims: list[dict[str, Any]] = []
    findings: list[str] = []
    components = (
        root / "agents",
        root / "agents" / "runtime",
        claims_dir,
    )
    for index, component in enumerate(components):
        try:
            metadata = component.lstat()
        except FileNotFoundError:
            if index == len(components) - 1:
                return claims, findings
            findings.append("active-claim-store-integrity-invalid")
            return claims, findings
        except OSError:
            findings.append("active-claim-store-integrity-invalid")
            return claims, findings
        if (
            _claim_store_component_is_alias(metadata)
            or not stat.S_ISDIR(metadata.st_mode)
        ):
            findings.append("active-claim-store-integrity-invalid")
            return claims, findings
    try:
        canonical_claims_dir = claims_dir.absolute()
        resolved_claims_dir = claims_dir.resolve(strict=True)
    except (FileNotFoundError, OSError, RuntimeError):
        findings.append("active-claim-store-integrity-invalid")
        return claims, findings
    if (
        resolved_claims_dir != canonical_claims_dir
        or not resolved_claims_dir.is_dir()
    ):
        findings.append("active-claim-store-integrity-invalid")
        return claims, findings
    try:
        with os.scandir(claims_dir) as entries:
            claim_paths = sorted(
                claims_dir / entry.name
                for entry in entries
                if entry.name.startswith("CLAIM-")
                and entry.name.endswith(".json")
            )
    except OSError:
        findings.append("active-claim-store-integrity-invalid")
        return claims, findings
    for path in claim_paths:
        try:
            metadata = path.lstat()
            if (
                _claim_store_component_is_alias(metadata)
                or not stat.S_ISREG(metadata.st_mode)
            ):
                findings.append(f"active-claim-integrity-invalid:{path.name}")
                continue
            resolved_path = path.resolve(strict=True)
        except (FileNotFoundError, OSError, RuntimeError):
            findings.append(f"active-claim-integrity-invalid:{path.name}")
            continue
        if (
            resolved_path != path.absolute()
            or resolved_path.parent != resolved_claims_dir
            or not resolved_path.is_file()
        ):
            findings.append(f"active-claim-integrity-invalid:{path.name}")
            continue
        try:
            payload = json.loads(resolved_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            findings.append(f"active-claim-invalid-json:{path.name}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"active-claim-invalid-root:{path.name}")
            continue
        status = str(payload.get("status") or "").strip()
        if status not in ACTIVE_CLAIM_STATUSES or _claim_is_overlay(payload):
            continue
        claim_id = str(payload.get("claim_id") or "").strip()
        if (
            payload.get("schema") != "agent-runtime-task-claim/v1"
            or not claim_id
            or path.name != f"{claim_id}.json"
            or not _claim_authority_shape_valid(payload)
        ):
            findings.append(f"active-claim-integrity-invalid:{path.name}")
            continue
        claims.append(payload)
    ordered = sorted(
        claims,
        key=lambda row: (
            str(row.get("updated_at") or row.get("last_heartbeat") or ""),
            str(row.get("claim_id") or ""),
        ),
        reverse=True,
    )
    return ordered, findings


def _claim_unit_path(root: Path, claim: dict[str, Any]) -> Path | None:
    raw_unit = claim.get("unit_id")
    if "unit_id" in claim and not isinstance(raw_unit, str):
        return None
    claimed_unit = raw_unit.strip() if isinstance(raw_unit, str) else ""
    raw_unit_spec = claim.get("unit_spec")
    if claimed_unit:
        if not isinstance(raw_unit_spec, str):
            return None
        unit_spec = raw_unit_spec.strip()
        if not unit_spec:
            return None
        try:
            normalized = compound_record.normalize_ref(unit_spec)
        except compound_record.CompoundRecordError:
            return None
        canonical = _work_item_path(root, claimed_unit)
        if canonical is None:
            return None
        try:
            expected_ref = canonical.relative_to(root.resolve()).as_posix()
        except ValueError:
            return None
        if normalized != expected_ref:
            return None
        candidate = root.resolve() / normalized
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root.resolve())
        except (FileNotFoundError, OSError, ValueError):
            return None
        if candidate.is_symlink() or resolved != candidate.absolute():
            return None
        return candidate if candidate.is_file() else None
    if "unit_spec" in claim and (
        not isinstance(raw_unit_spec, str) or raw_unit_spec.strip()
    ):
        return None
    raw_task = claim.get("task_id")
    if not isinstance(raw_task, str) or not raw_task.strip():
        return None
    return _work_item_path(root, raw_task.strip())


def _canonical_path_identity(path: Path) -> tuple[str, str, str]:
    """Derive task/unit/work identity from one canonical work-item path."""

    candidate = path.absolute()
    stem = candidate.stem
    unit_match = re.fullmatch(r"UNIT-(TASK-AR-\d+)-\d{3}", stem)
    if (
        unit_match
        and candidate.parent.name == unit_match.group(1)
        and candidate.parent.parent.name == "units"
        and candidate.parent.parent.parent.name == "tasks"
        and candidate.parent.parent.parent.parent.name == "lead_engineer"
        and candidate.parent.parent.parent.parent.parent.name == "agents"
    ):
        return unit_match.group(1), stem, stem
    if (
        re.fullmatch(r"TASK-AR-\d+", stem)
        and candidate.parent.name == "tasks"
        and candidate.parent.parent.name == "lead_engineer"
        and candidate.parent.parent.parent.name == "agents"
    ):
        return stem, "", stem
    return "", "", ""


def _canonical_identity(
    path: Path,
    meta: dict[str, Any],
) -> tuple[str, str, str]:
    task_id, unit_id, work_id = _canonical_path_identity(path)
    if not work_id:
        return "", "", ""

    def declared_identity_matches(field: str, expected: str) -> bool:
        if field not in meta:
            return True
        value = meta[field]
        return isinstance(value, str) and value == expected

    expected_kind = "unit" if unit_id else "task"
    if not declared_identity_matches("kind", expected_kind):
        return "", "", ""
    for field in ("work_id", "id", "display_id"):
        if not declared_identity_matches(field, work_id):
            return "", "", ""
    if not declared_identity_matches("task_id", task_id):
        return "", "", ""
    if unit_id:
        if not declared_identity_matches("unit_id", unit_id):
            return "", "", ""
        if not declared_identity_matches("parent_id", task_id):
            return "", "", ""
    elif "unit_id" in meta:
        return "", "", ""
    return task_id, unit_id, work_id


def _claim_matches_canonical(
    root: Path,
    claim: dict[str, Any],
    path: Path,
    meta: dict[str, Any],
) -> bool:
    task_id, unit_id, work_id = _canonical_identity(path, meta)
    raw_claim_task = claim.get("task_id")
    raw_claim_unit = claim.get("unit_id")
    if not isinstance(raw_claim_task, str):
        return False
    if "unit_id" in claim and not isinstance(raw_claim_unit, str):
        return False
    claim_task = raw_claim_task.strip()
    claim_unit = (
        raw_claim_unit.strip() if isinstance(raw_claim_unit, str) else ""
    )
    if claim_task != task_id:
        return False
    if unit_id:
        if claim_unit != unit_id:
            return False
        claim_path = _claim_unit_path(root, claim)
        return claim_path is not None and claim_path.resolve() == path.resolve()
    if work_id.startswith("TASK-"):
        if claim_unit:
            claim_path = _claim_unit_path(root, claim)
            canonical_unit_path = _work_item_path(root, claim_unit)
            if (
                claim_path is None
                or canonical_unit_path is None
                or claim_path.resolve() != canonical_unit_path.resolve()
            ):
                return False
            claim_meta = _read_work(claim_path) if claim_path else None
            if not claim_meta:
                return False
            linked_task, linked_unit, _linked_work = _canonical_identity(
                claim_path, claim_meta
            )
            return linked_task == task_id and linked_unit == claim_unit
        if "unit_spec" not in claim:
            return True
        raw_unit_spec = claim.get("unit_spec")
        return isinstance(raw_unit_spec, str) and not raw_unit_spec.strip()
    return False


def _claim_may_target_canonical(
    root: Path,
    claim: dict[str, Any],
    path: Path,
    meta: dict[str, Any],
) -> bool:
    task_id, unit_id, _work_id = _canonical_identity(path, meta)
    if str(claim.get("task_id") or "").strip() == task_id:
        return True
    if unit_id and str(claim.get("unit_id") or "").strip() == unit_id:
        return True
    claim_path = _claim_unit_path(root, claim)
    return claim_path is not None and claim_path.resolve() == path.resolve()


def _merge_claim_authority(
    meta: dict[str, Any],
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    merged = dict(meta)
    for field in CLAIM_AUTHORITY_FIELDS:
        merged[field] = list(
            dict.fromkeys(
                value
                for source in (meta, *claims)
                for value in _list_value(source.get(field))
            )
        )
    return merged


def resolve_active_work_contexts(
    root: Path,
    *,
    work_id: str | None = None,
) -> dict[str, Any]:
    """Resolve one immutable active-claim authority snapshot.

    Explicit work selects claims only from the current worktree (or an
    unbound legacy claim that names the canonical work). Inferred Stop selects
    exactly one non-overlay claim for the current linked worktree. Any selected
    claim must agree on task, unit, and unit-spec identity before its authority
    fields can be merged.
    """

    root = Path(root).resolve()
    claims, claim_findings = _active_claims(root)
    if claim_findings:
        return {
            "contexts": [],
            "linked_mode": True,
            "reason": "active-claim-context-invalid",
            "selected_claim_ids": [],
            "findings": claim_findings,
        }
    primary_root = _git_primary_root(root)
    selected: list[dict[str, Any]] = []
    canonical_path: Path | None = None
    canonical_meta: dict[str, Any] | None = None

    if work_id:
        canonical_path = _work_item_path(root, work_id)
        canonical_meta = _read_work(canonical_path) if canonical_path else None
        if not canonical_path or not canonical_meta:
            return {
                "contexts": [],
                "linked_mode": False,
                "reason": None,
                "selected_claim_ids": [],
            }
        for claim in claims:
            raw_worktree = str(claim.get("worktree_path") or "").strip()
            resolved_worktree = _resolved_claim_worktree(
                root,
                raw_worktree,
                primary_root=primary_root,
            )
            if raw_worktree:
                if resolved_worktree is not None and resolved_worktree == root:
                    selected.append(claim)
                continue
            if _claim_may_target_canonical(
                root, claim, canonical_path, canonical_meta
            ):
                selected.append(claim)
    else:
        bound_matches: list[dict[str, Any]] = []
        unbound: list[dict[str, Any]] = []
        for claim in claims:
            raw_worktree = str(claim.get("worktree_path") or "").strip()
            if not raw_worktree:
                unbound.append(claim)
                continue
            resolved_worktree = _resolved_claim_worktree(
                root,
                raw_worktree,
                primary_root=primary_root,
            )
            if resolved_worktree is not None and resolved_worktree == root:
                bound_matches.append(claim)
        selected = bound_matches if bound_matches else unbound

    if len(selected) > 1:
        return {
            "contexts": [],
            "linked_mode": True,
            "reason": "active-claim-context-ambiguous",
            "selected_claim_ids": [],
        }
    if not selected:
        contexts = [canonical_meta] if canonical_meta else []
        return {
            "contexts": contexts,
            "linked_mode": bool(canonical_meta),
            "reason": None,
            "selected_claim_ids": [],
        }

    claim = selected[0]
    if canonical_path is None:
        canonical_path = _claim_unit_path(root, claim)
        canonical_meta = _read_work(canonical_path) if canonical_path else None
    if (
        canonical_path is None
        or canonical_meta is None
        or not _claim_matches_canonical(
            root, claim, canonical_path, canonical_meta
        )
    ):
        return {
            "contexts": [],
            "linked_mode": True,
            "reason": "active-claim-context-invalid",
            "selected_claim_ids": [],
        }
    return {
        "contexts": [_merge_claim_authority(canonical_meta, [claim])],
        "linked_mode": True,
        "reason": None,
        "selected_claim_ids": [str(claim.get("claim_id") or "").strip()],
    }


def _active_work_contexts(
    root: Path, *, work_id: str | None = None
) -> list[dict[str, Any]]:
    """Compatibility wrapper for callers that need only resolved metadata."""

    resolution = resolve_active_work_contexts(root, work_id=work_id)
    if resolution["contexts"]:
        return list(resolution["contexts"])
    reason = str(resolution.get("reason") or "").strip()
    if reason:
        return [{"work_id": f"__{reason.replace('-', '_')}__"}]
    return []


def _accepted_work_ids(meta: dict[str, Any]) -> set[str]:
    values = {
        str(meta.get(field) or "").strip()
        for field in ("work_id", "task_id", "unit_id")
    }
    parent = str(meta.get("parent_id") or "").strip()
    if parent.startswith("TASK-"):
        values.add(parent)
    return {value for value in values if value}


def _parent_task_context(
    root: Path,
    meta: dict[str, Any],
) -> dict[str, Any] | None:
    current_id = str(
        meta.get("unit_id") or meta.get("work_id") or meta.get("id") or ""
    ).strip()
    task_id = str(meta.get("task_id") or meta.get("parent_id") or "").strip()
    if not task_id.startswith("TASK-") or task_id == current_id:
        return None
    path = _work_item_path(root, task_id)
    return _read_work(path) if path else None


def _repeat_contexts(
    root: Path,
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    seen: set[str] = set()
    for meta in contexts:
        for candidate in (meta, _parent_task_context(root, meta)):
            if not candidate:
                continue
            identity = str(
                candidate.get("unit_id")
                or candidate.get("work_id")
                or candidate.get("id")
                or candidate.get("display_id")
                or id(candidate)
            ).strip()
            if identity in seen:
                continue
            seen.add(identity)
            expanded.append(candidate)
    return expanded


def _normalized_trigger(value: object) -> str:
    return re.sub(
        r"[^a-z0-9]+", "_", str(value or "").strip().lower()
    ).strip("_")


def repeated_failure_requirement(
    root: Path,
    contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    expanded = _repeat_contexts(root, contexts)
    work_ids: set[str] = set()
    for meta in expanded:
        work_ids.update(_accepted_work_ids(meta))

    findings: list[str] = []
    raw_signatures = [
        signature
        for meta in expanded
        for signature in _list_value(meta.get("defect_signatures"))
    ]
    raw_compound_refs = [
        ref
        for meta in expanded
        for ref in _list_value(meta.get("compound_refs"))
    ]
    try:
        signatures = compound_record.normalize_signatures(raw_signatures)
    except compound_record.CompoundRecordError as exc:
        signatures = []
        findings.extend(exc.findings)
    try:
        compound_refs = list(
            dict.fromkeys(
                compound_record.normalize_ref(ref)
                for ref in raw_compound_refs
            )
        )
    except compound_record.CompoundRecordError as exc:
        compound_refs = []
        findings.extend(exc.findings)

    triggers = list(
        dict.fromkeys(
            trigger
            for meta in expanded
            for raw in _list_value(meta.get("escalation_triggers"))
            if (trigger := _normalized_trigger(raw))
        )
    )
    required = bool(raw_signatures or "repeated_failure" in triggers)
    valid_refs: list[str] = []
    if required:
        for ref in compound_refs:
            try:
                _path, record = compound_record.load_record_ref(root, ref)
            except compound_record.CompoundRecordError as exc:
                findings.extend(f"{ref}:{finding}" for finding in exc.findings)
                continue
            if not work_ids.intersection(record["work_ids"]):
                findings.append(f"{ref}:compound:current-work-mismatch")
                continue
            prevention_findings = (
                compound_record.validate_prevention_destinations(
                    root,
                    record,
                    current_work_ids=work_ids,
                )
            )
            findings.extend(
                f"{ref}:{finding}" for finding in prevention_findings
            )
            if not prevention_findings:
                valid_refs.append(ref)
        if not valid_refs:
            findings.append("compound:current-work-record-required")

    findings = list(dict.fromkeys(findings))
    return {
        "required": required,
        "satisfied": bool(required and valid_refs and not findings),
        "defect_signatures": signatures,
        "escalation_triggers": triggers,
        "compound_refs": compound_refs,
        "valid_compound_refs": valid_refs,
        "findings": findings,
    }


def _review_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    meta, _body = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
    return dict(meta)


def _payload_links(
    payload: dict[str, Any],
    *,
    work_ids: set[str],
    defect_signatures: list[str],
) -> bool:
    linked_work = {
        str(payload.get(field) or "").strip()
        for field in ("work_id", "task_id", "unit_id")
    }
    if linked_work.intersection(work_ids):
        return True
    try:
        linked_signatures = set(
            compound_record.normalize_signatures(
                _list_value(payload.get("defect_signatures"))
            )
        )
    except compound_record.CompoundRecordError:
        return False
    return bool(linked_signatures.intersection(defect_signatures))


def _linked_closure_records(
    root: Path, contexts: list[dict[str, Any]]
) -> dict[str, bool]:
    found = {"compound": False, "review": False, "retro": False}
    repeat_contexts = _repeat_contexts(root, contexts)
    work_ids = {
        work_id
        for meta in repeat_contexts
        for work_id in _accepted_work_ids(meta)
    }
    try:
        signatures = compound_record.normalize_signatures(
            [
                signature
                for meta in repeat_contexts
                for signature in _list_value(meta.get("defect_signatures"))
            ]
        )
    except compound_record.CompoundRecordError:
        signatures = []
    for meta in repeat_contexts:
        for ref in _list_value(meta.get("compound_refs")):
            try:
                _path, record = compound_record.load_record_ref(root, ref)
            except compound_record.CompoundRecordError:
                continue
            if compound_record.record_links(
                record,
                work_ids=work_ids,
                defect_signatures=signatures,
            ):
                found["compound"] = True

    for meta in contexts:
        work_ids = _accepted_work_ids(meta)
        try:
            signatures = compound_record.normalize_signatures(
                _list_value(meta.get("defect_signatures"))
            )
        except compound_record.CompoundRecordError:
            continue
        for ref in _list_value(meta.get("review_refs")):
            try:
                normalized = compound_record.normalize_ref(ref)
                path = root / normalized
                if not path.is_file():
                    continue
                payload = _review_payload(path)
            except (
                OSError,
                json.JSONDecodeError,
                compound_record.CompoundRecordError,
            ):
                continue
            if not _payload_links(
                payload,
                work_ids=work_ids,
                defect_signatures=signatures,
            ):
                continue
            if path.name.startswith("RETRO-"):
                found["retro"] = True
            else:
                found["review"] = True
    return found


def _legacy_date_records(
    root: Path, *, now: str | datetime | None = None
) -> dict[str, bool]:
    moment = _coerce_now(now)
    today = moment.date().isoformat()
    compound = False
    compound_log = root / "agents" / "lead_engineer" / "compound_log.md"
    if compound_log.exists():
        try:
            compound = f"COMPOUND-{today}" in compound_log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            compound = False
    reviews = root / "reviews"
    review = bool(list(reviews.glob(f"REVIEW-{today}-*.md"))) if reviews.is_dir() else False
    retro = bool(list(reviews.glob(f"RETRO-{today}-*.md"))) if reviews.is_dir() else False
    return {"compound": compound, "review": review, "retro": retro}


def has_closure_record(
    root: Path,
    *,
    now: str | datetime | None = None,
    work_id: str | None = None,
    _resolution: dict[str, Any] | None = None,
) -> dict[str, bool]:
    root = Path(root).resolve()
    resolution = _resolution or resolve_active_work_contexts(
        root, work_id=work_id
    )
    contexts = list(resolution["contexts"])
    if contexts:
        return _linked_closure_records(root, contexts)
    if resolution.get("linked_mode"):
        return {"compound": False, "review": False, "retro": False}
    return _legacy_date_records(root, now=now)


def decide(
    substantial_lines: int,
    records: dict[str, bool],
    *,
    threshold: int,
    disabled: bool,
    now_lines: int | None = None,
    repeat_failure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lines = now_lines if now_lines is not None else substantial_lines
    if disabled:
        return {"decision": "approve", "reason": "closure-gate-disabled", "substantial": False, "missing": [], "message": ""}
    repeat_failure = repeat_failure or {
        "required": False,
        "satisfied": False,
        "findings": [],
    }
    if repeat_failure.get("required"):
        if not repeat_failure.get("satisfied"):
            return {
                "decision": "block",
                "reason": "repeated-failure-compound-required",
                "substantial": substantial_lines >= threshold,
                "missing": ["compound"],
                "message": (
                    "Declared repeated-failure work requires a canonical "
                    "Compound linked to the current task or unit, and every "
                    "prevention ref must stay inside the repository and exist. "
                    "At least one prevention destination must be a regression "
                    "fixture, executable *_gate.py, task proposal, or accepted "
                    "watch state."
                ),
            }
        return {
            "decision": "approve",
            "reason": "repeated-failure-compound-present",
            "substantial": substantial_lines >= threshold,
            "missing": [],
            "message": "current-work Compound and supported prevention destination present",
        }
    if substantial_lines < threshold:
        return {"decision": "approve", "reason": "not-substantial", "substantial": False, "missing": [], "message": ""}
    present = [kind for kind in RECORD_KINDS if records.get(kind)]
    if present:
        return {
            "decision": "approve",
            "reason": "closure-record-present",
            "substantial": True,
            "missing": [],
            "message": f"closure records today: {', '.join(present)}",
        }
    message = (
        f"Substantial work today (~{lines} code lines changed in src/scripts/tests) has no "
        "closure record. The canonical cycle is plan -> work -> verification -> compound -> "
        "review -> retro. Record at least one before closing: a COMPOUND-<date> entry in "
        "agents/lead_engineer/compound_log.md (when a recurring failure occurred), a "
        "reviews/REVIEW-<date>-*-closeout.md, and/or a reviews/RETRO-<date>-*.md. "
        "Escape: AGENT_RUNTIME_CLOSURE_GATE_DISABLE=1."
    )
    return {
        "decision": "block",
        "reason": "closure-records-missing",
        "substantial": True,
        "missing": list(RECORD_KINDS),
        "message": message,
    }


def apply_scribe_obligation(
    result: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    substantial_lines: int,
    threshold: int,
    disabled: bool,
) -> dict[str, Any]:
    """Add independent Scribe obligations without weakening closure evidence."""

    source_debt = evaluation.get("source_debt")
    if not isinstance(source_debt, dict):
        source_debt = {"status": evaluation.get("state", "unavailable")}
    unavailable_sources = _list_value(source_debt.get("unavailable_sources"))
    summary = {
        "state": evaluation.get("state", "unavailable"),
        "readiness": evaluation.get("readiness", "advisory"),
        "source_debt": source_debt,
        "unavailable_sources": unavailable_sources,
        "projection": evaluation.get(
            "projection", {"path": "", "status": "missing"}
        ),
        "active_coverage": evaluation.get(
            "active_coverage", {"status": "incomplete"}
        ),
        "cleanup_plan": evaluation.get(
            "cleanup_plan", {"status": "unavailable", "candidate_count": 0}
        ),
        "cleanup_outcome": evaluation.get(
            "cleanup_outcome", {"status": "none", "valid": True}
        ),
        "overdue_sources": list(evaluation.get("overdue_sources", [])),
        "closure_blocking": bool(evaluation.get("closure_blocking")),
        "closure_reasons": list(evaluation.get("closure_reasons", [])),
    }
    result["scribe"] = summary
    if (
        disabled
        or substantial_lines < threshold
        or not summary["closure_blocking"]
    ):
        return result

    if "configured-source-integrity" in summary["closure_reasons"]:
        paths = (
            ", ".join(unavailable_sources)
            or "(configured source path unavailable)"
        )
        missing_name = "scribe_source_integrity"
        message = (
            f"Configured canonical Scribe source integrity failed for: {paths}. "
            "Repair the configured canonical source before closure; refreshing "
            "or writing the bounded projection cannot clear this obligation."
        )
        if result["decision"] == "approve":
            result.update(
                {
                    "decision": "block",
                    "reason": "scribe-source-integrity",
                    "missing": [missing_name],
                    "message": message,
                }
            )
        else:
            existing_missing = list(result.get("missing", []))
            if missing_name not in existing_missing:
                existing_missing.append(missing_name)
            result["missing"] = existing_missing
            result["message"] = (
                str(result.get("message") or "") + " " + message
            ).strip()
        return result

    reason_contract = {
        "source-debt-overdue": (
            "scribe_source_debt",
            "Canonical source debt is still overdue. Complete an explicitly "
            "authorized cleanup, or cite an explicit owner no-touch decision.",
        ),
        "projection-not-fresh": (
            "scribe_projection",
            "Refresh the bounded view with "
            "`python scripts/scribe_due.py --write-projection`.",
        ),
        "active-coverage-incomplete": (
            "scribe_active_coverage",
            "Refresh the bounded view so every current task and non-overlay "
            "claim identity is represented.",
        ),
        "cleanup-outcome-invalid": (
            "scribe_cleanup_outcome",
            "The cleanup receipt is invalid. Re-record the completed cleanup "
            "with a valid authorization and bound before/after evidence.",
        ),
    }
    obligations = [
        (reason, *reason_contract[reason])
        for reason in summary["closure_reasons"]
        if reason in reason_contract
    ]
    if not obligations:
        obligations = [
            (
                "state-obligation",
                "scribe_state",
                "Resolve the blocking Scribe state before closure.",
            )
        ]
    missing = [missing_name for _reason, missing_name, _detail in obligations]
    detail = " ".join(message for _reason, _missing, message in obligations)
    projection = summary["projection"]
    message = (
        f"{detail} The projection is only a bounded view, not proof that "
        "canonical cleanup occurred. "
        f"Projection path: {projection.get('path', state_projection.DEFAULT_PROJECTION_PATH)} "
        f"(status={projection.get('status', 'missing')})."
    )
    if result["decision"] == "approve":
        result.update(
            {
                "decision": "block",
                "reason": f"scribe-{obligations[0][0]}",
                "missing": missing,
                "message": message,
            }
        )
    else:
        existing_missing = list(result.get("missing", []))
        for missing_name in missing:
            if missing_name not in existing_missing:
                existing_missing.append(missing_name)
        result["missing"] = existing_missing
        result["message"] = (str(result.get("message") or "") + " " + message).strip()
    return result


def assess(
    root: Path,
    *,
    now: str | datetime | None = None,
    work_id: str | None = None,
    threshold: int | None = None,
    window_hours: int | None = None,
    disabled: bool | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    moment = _coerce_now(now)
    threshold = _env_int("AGENT_RUNTIME_CLOSURE_GATE_THRESHOLD", DEFAULT_THRESHOLD) if threshold is None else threshold
    window_hours = _env_int("AGENT_RUNTIME_CLOSURE_GATE_WINDOW_HOURS", DEFAULT_WINDOW_HOURS) if window_hours is None else window_hours
    disabled = _env_bool("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", False) if disabled is None else disabled
    lines = count_substantial_lines(root, now=moment, window_hours=window_hours)
    resolution = resolve_active_work_contexts(root, work_id=work_id)
    contexts = list(resolution["contexts"])
    records = has_closure_record(
        root,
        now=moment,
        work_id=work_id,
        _resolution=resolution,
    )
    repeat_failure = repeated_failure_requirement(
        root,
        contexts,
    )
    result = decide(
        lines,
        records,
        threshold=threshold,
        disabled=disabled,
        now_lines=lines,
        repeat_failure=repeat_failure,
    )
    resolution_reason = str(resolution.get("reason") or "").strip()
    if resolution_reason and not disabled:
        result = {
            "decision": "block",
            "reason": resolution_reason,
            "substantial": lines >= threshold,
            "missing": ["work_id"],
            "message": (
                "Active claim authority could not be bound to exactly one "
                "canonical task/unit identity. Supply an explicit work ID or "
                "repair the claim identity before closure."
            ),
        }
    try:
        scribe_evaluation = state_projection.evaluate_state(root)
    except Exception as exc:
        scribe_evaluation = {
            "state": "unavailable",
            "readiness": "advisory",
            "projection": {
                "path": state_projection.DEFAULT_PROJECTION_PATH,
                "status": "unavailable",
            },
            "overdue_sources": [],
            "closure_blocking": False,
            "error": str(exc),
        }
    result = apply_scribe_obligation(
        result,
        scribe_evaluation,
        substantial_lines=lines,
        threshold=threshold,
        disabled=disabled,
    )
    result["substantial_lines"] = lines
    result["records"] = records
    result["repeat_failure"] = repeat_failure
    result["threshold"] = threshold
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Closure gate: require compound/review/retro for substantial work")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--now")
    parser.add_argument(
        "--work-id",
        help="Resolve closure records against this task/unit instead of inferring active claims",
    )
    parser.add_argument("--check", action="store_true", help="exit nonzero when closure records are missing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = assess(args.root, now=args.now, work_id=args.work_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"closure-gate: {result['decision']} ({result['reason']}); "
              f"lines={result['substantial_lines']} records={result['records']}")
        if result["message"]:
            print(result["message"])
    if args.check and result["decision"] == "block":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
