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
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 80
DEFAULT_WINDOW_HOURS = 12
CODE_PATHS = ("src", "scripts", "tests")
RECORD_KINDS = ("compound", "review", "retro")


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


def has_closure_record(root: Path, *, now: str | datetime | None = None) -> dict[str, bool]:
    moment = _coerce_now(now)
    today = moment.date().isoformat()
    root = Path(root)
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


def decide(
    substantial_lines: int,
    records: dict[str, bool],
    *,
    threshold: int,
    disabled: bool,
    now_lines: int | None = None,
) -> dict[str, Any]:
    lines = now_lines if now_lines is not None else substantial_lines
    if disabled:
        return {"decision": "approve", "reason": "closure-gate-disabled", "substantial": False, "missing": [], "message": ""}
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


def assess(
    root: Path,
    *,
    now: str | datetime | None = None,
    threshold: int | None = None,
    window_hours: int | None = None,
    disabled: bool | None = None,
) -> dict[str, Any]:
    moment = _coerce_now(now)
    threshold = _env_int("AGENT_RUNTIME_CLOSURE_GATE_THRESHOLD", DEFAULT_THRESHOLD) if threshold is None else threshold
    window_hours = _env_int("AGENT_RUNTIME_CLOSURE_GATE_WINDOW_HOURS", DEFAULT_WINDOW_HOURS) if window_hours is None else window_hours
    disabled = _env_bool("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", False) if disabled is None else disabled
    lines = count_substantial_lines(root, now=moment, window_hours=window_hours)
    records = has_closure_record(root, now=moment)
    result = decide(lines, records, threshold=threshold, disabled=disabled, now_lines=lines)
    result["substantial_lines"] = lines
    result["records"] = records
    result["threshold"] = threshold
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Closure gate: require compound/review/retro for substantial work")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--now")
    parser.add_argument("--check", action="store_true", help="exit nonzero when closure records are missing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = assess(args.root, now=args.now)
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
