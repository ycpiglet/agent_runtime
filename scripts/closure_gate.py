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


def _active_work_contexts(
    root: Path, *, work_id: str | None = None
) -> list[dict[str, Any]]:
    """Return explicit or actively claimed work metadata.

    The linked mode is intentionally unavailable when no canonical work item
    can be resolved. That preserves legacy date-based behavior for old hosts
    without allowing an unrelated same-day file to satisfy a known claim.
    """
    if work_id:
        path = _work_item_path(root, work_id)
        meta = _read_work(path) if path else None
        return [meta] if meta else []

    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims: list[dict[str, Any]] = []
    if claims_dir.is_dir():
        for path in sorted(claims_dir.glob("CLAIM-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                isinstance(payload, dict)
                and str(payload.get("status") or "").strip()
                in ACTIVE_CLAIM_STATUSES
            ):
                claims.append(payload)

    ordered_claims = sorted(
        claims,
        key=lambda row: (
            str(row.get("updated_at") or row.get("last_heartbeat") or ""),
            str(row.get("claim_id") or ""),
        ),
        reverse=True,
    )
    matching_claims: list[dict[str, Any]] = []
    for claim in ordered_claims:
        worktree = str(claim.get("worktree_path") or "").strip()
        if not worktree:
            continue
        try:
            if Path(worktree).resolve() == root.resolve():
                matching_claims.append(claim)
        except OSError:
            continue
    candidates = matching_claims or ordered_claims
    if len(candidates) > 1:
        # A global Stop hook cannot safely guess which of several active
        # claims the caller intends to close. A non-linking sentinel keeps the
        # gate fail-closed; callers can disambiguate with --work-id.
        return [{"work_id": "__ambiguous_active_claim__"}]

    contexts: list[dict[str, Any]] = []
    for claim in candidates:
        path: Path | None = None
        unit_spec = str(claim.get("unit_spec") or "").strip()
        if unit_spec:
            candidate = root / unit_spec
            if candidate.is_file():
                path = candidate
        claimed_work = str(
            claim.get("unit_id") or claim.get("task_id") or ""
        ).strip()
        if path is None and claimed_work:
            path = _work_item_path(root, claimed_work)
        meta = _read_work(path) if path else None
        resolved = str((meta or {}).get("work_id") or claimed_work).strip()
        if meta and resolved:
            contexts.append(meta)
    return contexts


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
) -> dict[str, bool]:
    root = Path(root).resolve()
    contexts = _active_work_contexts(root, work_id=work_id)
    if contexts:
        return _linked_closure_records(root, contexts)
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
    moment = _coerce_now(now)
    threshold = _env_int("AGENT_RUNTIME_CLOSURE_GATE_THRESHOLD", DEFAULT_THRESHOLD) if threshold is None else threshold
    window_hours = _env_int("AGENT_RUNTIME_CLOSURE_GATE_WINDOW_HOURS", DEFAULT_WINDOW_HOURS) if window_hours is None else window_hours
    disabled = _env_bool("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", False) if disabled is None else disabled
    lines = count_substantial_lines(root, now=moment, window_hours=window_hours)
    records = has_closure_record(root, now=moment, work_id=work_id)
    repeat_failure = repeated_failure_requirement(
        Path(root).resolve(),
        _active_work_contexts(Path(root).resolve(), work_id=work_id),
    )
    result = decide(
        lines,
        records,
        threshold=threshold,
        disabled=disabled,
        now_lines=lines,
        repeat_failure=repeat_failure,
    )
    try:
        scribe_evaluation = state_projection.evaluate_state(Path(root))
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
