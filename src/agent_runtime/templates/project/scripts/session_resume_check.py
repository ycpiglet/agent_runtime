#!/usr/bin/env python3
"""Crash-recovery + session-resume auditor (report-only, non-blocking).

Purpose
-------
When a fresh agent (or a SessionStart hook) starts a new session — possibly
after a sudden PC shutdown — this script prints ONE crisp "RESUME HERE" block
and flags any inconsistent / zombie state, so the stopping point is immediately
knowable and a *different* agent in a *different* session can resume safely.

It reports:
  - RESUME HERE: the authoritative current state from
    ``agents/project/NEXT-SESSION-POINTER.yml`` + ``agents/lead_engineer/STATUS.md``
    + ``.claude/ralph-loop.local.md``.
  - CRASH SCAN: stale claim files, inbox messages stuck in ``claimed`` with a
    stale/missing claim, and *candidate-abandoned* sessions (age-based, because
    session records do NOT carry a pid so we cannot prove death).
  - WARNINGS: human strings describing every anomaly.

Safety contract
----------------
This is a resume-check, so it must NEVER crash a session start. The CLI ALWAYS
exits 0 unless ``--strict`` is passed. The main body is wrapped so any
unexpected exception prints a single ``WARN`` line and still exits 0.

The only mutating action is ``--fix``, which calls
``message_queue.recover_stale_claim`` on inbox messages whose claim is stale,
resetting them back to ``open``. Nothing else writes anything.

The core scanners are PURE: they take explicit directory paths and a ``now``
epoch so unit tests can use temp dirs and never touch the real repo.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re as _re
import sys
from pathlib import Path

# Windows cp949/legacy consoles cannot encode em-dashes (—) in status text and
# the report would degrade to a single WARN line; force UTF-8 so a SessionStart
# hook always gets the full RESUME HERE block (same guard as
# run_daily_summary.py). Must never crash the resume check itself.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Reuse the vendored message_queue helpers (same scripts/ dir).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import message_queue as mq  # noqa: E402


# --- datetime parsing helper ---

def _parse_iso_epoch(value: object) -> float | None:
    """Parse an ISO8601 timestamp (``+09:00`` or trailing ``Z``) to epoch.

    Returns None when the value is missing or unparseable (treat age as
    unknown rather than crashing).
    """
    if not isinstance(value, str):
        return None
    text = value.strip().strip('"').strip("'")
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = _dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.timestamp()


# --- pure scanners ---

def scan_stale_claims(claims_dir: Path, now: float) -> list[dict]:
    """Return one record per stale ``*.claim`` file in ``claims_dir``.

    Ignores ``.gitkeep`` / dotfiles / non-files. Skips files that read as None.
    """
    out: list[dict] = []
    if not claims_dir.is_dir():
        return out
    for path in sorted(claims_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.suffix != ".claim":
            continue
        claim = mq._read_claim(path)
        if claim is None:
            continue
        if not mq._is_stale_claim(claim, now):
            continue
        expires_at = claim.get("expires_at")
        try:
            age_seconds: int | None = round(now - float(expires_at))
        except (TypeError, ValueError):
            age_seconds = None
        out.append({
            "file": path.name,
            "pid": claim.get("pid"),
            "expires_at": expires_at,
            "age_seconds": age_seconds,
        })
    return out


def scan_claimed_stale_messages(inbox_dir: Path, claims_dir: Path,
                                now: float) -> list[dict]:
    """Flag inbox messages stuck in ``claimed`` with a stale/missing claim."""
    out: list[dict] = []
    if not inbox_dir.is_dir():
        return out
    for path in sorted(inbox_dir.iterdir()):
        if not path.is_file() or path.suffix != ".md" or path.name.startswith("."):
            continue
        try:
            meta, _ = mq.parse_frontmatter(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not meta or meta.get("status") != "claimed":
            continue
        message_id = mq._msg_id_from_path(path, meta)
        # Derive claim file: prefer mq._claim_path on the message id, but it is
        # rooted at the real CLAIMS_DIR; for arbitrary claims_dir (tests) fall
        # back to matching by stem within claims_dir.
        claim_file = claims_dir / f"{message_id}.claim"
        if not claim_file.exists():
            claim_file = claims_dir / f"{path.stem}.claim"
        if not claim_file.exists():
            out.append({
                "file": path.name,
                "message_id": message_id,
                "reason": "missing-claim",
            })
            continue
        claim = mq._read_claim(claim_file)
        if claim is None or mq._is_stale_claim(claim, now):
            out.append({
                "file": path.name,
                "message_id": message_id,
                "reason": "stale-claim",
            })
    return out


def scan_dead_sessions(sessions_dir: Path, now: float,
                       max_age_seconds: float) -> list[dict]:
    """Return *candidate-abandoned* sessions (age-based, not pid-based).

    Session records carry no pid, so we cannot prove death. A session in
    ``spawning``/``active`` whose ``started_at`` is older than
    ``max_age_seconds`` is reported as a candidate for being abandoned after a
    crash. If ``sessions_dir`` is missing, return [].
    """
    out: list[dict] = []
    if not sessions_dir.is_dir():
        return out
    for path in sorted(sessions_dir.iterdir()):
        if not path.is_file() or path.suffix != ".json" or path.name.startswith("."):
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        if rec.get("status") not in {"spawning", "active"}:
            continue
        started_epoch = _parse_iso_epoch(rec.get("started_at"))
        if started_epoch is None:
            continue
        age = now - started_epoch
        if age <= max_age_seconds:
            continue
        out.append({
            "file": path.name,
            "agent_id": rec.get("agent_id"),
            "role": rec.get("role"),
            "task_id": rec.get("task_id"),
            "status": rec.get("status"),
            "age_seconds": round(age),
        })
    return out


def check_pointer_freshness(pointer_path: Path, now_iso: str,
                            max_age_hours: float) -> dict:
    """Read NEXT-SESSION-POINTER.yml with a minimal line scanner (no PyYAML).

    Extracts ``updated_at``, ``updated_by``, ``current_state.signal`` / ``score``
    and the FIRST non-empty indented line of the ``summary: >`` block scalar
    (NOT the whole history). Computes age in hours from ``now_iso``.
    """
    result = {
        "updated_at": None,
        "updated_by": None,
        "signal": None,
        "score": None,
        "summary_head": None,
        "age_hours": None,
        "stale": False,
        "exists": False,
    }
    if not pointer_path.is_file():
        return result
    result["exists"] = True
    try:
        lines = pointer_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return result

    in_current_state = False
    in_summary = False
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        # top-level keys (no leading whitespace)
        if line[:1] not in (" ", "\t"):
            in_summary = False
            if stripped.startswith("updated_at:"):
                result["updated_at"] = stripped.split(":", 1)[1].strip()
                continue
            if stripped.startswith("updated_by:"):
                result["updated_by"] = stripped.split(":", 1)[1].strip()
                continue
            in_current_state = stripped.startswith("current_state:")
            continue
        # indented keys under current_state
        if in_current_state:
            if in_summary:
                # first non-empty indented line after "summary: >"
                if stripped:
                    result["summary_head"] = stripped
                    in_summary = False
                continue
            if stripped.startswith("signal:"):
                result["signal"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("score:"):
                result["score"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("summary:"):
                after = stripped.split(":", 1)[1].strip()
                if after and after not in (">", "|", ">-", "|-"):
                    result["summary_head"] = after
                else:
                    in_summary = True

    updated_epoch = _parse_iso_epoch(result["updated_at"])
    now_epoch = _parse_iso_epoch(now_iso)
    if updated_epoch is not None and now_epoch is not None:
        age_hours = (now_epoch - updated_epoch) / 3600.0
        result["age_hours"] = age_hours
        result["stale"] = age_hours > max_age_hours
    return result


def check_ralph_consistency(ralph_path: Path, pointer: dict, now: float) -> dict:
    """Audit .claude/ralph-loop.local.md for blind-resume / staleness / drift.

    Heuristics (kept simple and documented):
      (a) active is true  -> a fresh agent might blindly resume; warn.
      (b) active true AND started_at older than ~3 days -> stale loop; warn.
      (c) active true but the loop body/frontmatter shows no recent linkage to
          the pointer's current task (drift) -> warn.
    """
    result = {
        "exists": False,
        "active": False,
        "iteration": None,
        "started_at": None,
        "age_days": None,
        "warnings": [],
    }
    if not ralph_path.is_file():
        return result
    result["exists"] = True
    try:
        text = ralph_path.read_text(encoding="utf-8")
    except Exception:
        return result
    meta, body = mq.parse_frontmatter(text)

    active_raw = str(meta.get("active", "")).strip().lower()
    result["active"] = active_raw in {"true", "yes", "1"}
    result["iteration"] = meta.get("iteration")
    started_at = meta.get("started_at")
    if isinstance(started_at, str):
        started_at = started_at.strip().strip('"').strip("'")
    result["started_at"] = started_at

    started_epoch = _parse_iso_epoch(started_at)
    if started_epoch is not None:
        result["age_days"] = (now - started_epoch) / 86400.0

    warnings: list[str] = []
    if result["active"]:
        # (a) blind-resume risk
        warnings.append(
            "ralph-loop active:true — a fresh agent might blindly resume; "
            "verify against pointer/STATUS before resuming")
        # (b) stale loop (~3 days)
        if result["age_days"] is not None and result["age_days"] > 3.0:
            warnings.append(
                f"ralph-loop active but started_at is {result['age_days']:.1f} "
                "days old (stale loop)")
        # (c) drift: active but no linkage to the pointer's current task
        pointer_head = ""
        if isinstance(pointer, dict):
            pointer_head = str(pointer.get("summary_head") or "")
        first_token = pointer_head.split()[0] if pointer_head.split() else ""
        if first_token and first_token not in text:
            warnings.append(
                "ralph-loop active but shows no recent linkage to the pointer's "
                f"current task ({first_token}); possible drift")
    result["warnings"] = warnings
    return result


# --- sub-step checkpoints (per-task append-only progress log) ---

def _checkpoint_file(checkpoints_dir: Path, task: str) -> Path:
    """Return the per-task checkpoint JSONL path with a sanitized filename.

    Keeps only ``[A-Za-z0-9._-]``; any run of other characters collapses to a
    single ``_``; leading/trailing ``_`` are stripped. An empty result falls
    back to ``task`` so we never produce a hidden or empty filename.
    """
    safe = _re.sub(r"[^A-Za-z0-9._-]+", "_", str(task)).strip("_")
    if not safe:
        safe = "task"
    return checkpoints_dir / f"{safe}.jsonl"


def append_checkpoint(checkpoints_dir: Path, *, task: str, step: str,
                      status: str = "started", next_action: str = "",
                      agent: str = "", now_iso: str) -> Path:
    """Append ONE checkpoint JSON line for ``task`` and return the file path.

    This is the only new mutating action; it must only run from the
    ``checkpoint`` subcommand and never from the audit path.
    """
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_file(checkpoints_dir, task)
    record = {
        "ts": now_iso,
        "task": task,
        "step": step,
        "status": status,
        "next": next_action,
        "agent": agent,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


_CLOSED_STATUSES = {"done", "complete", "completed", "closed"}


def read_latest_checkpoints(checkpoints_dir: Path) -> list[dict]:
    """Return the LAST record per ``*.jsonl`` file in ``checkpoints_dir``.

    Each returned dict gains a computed ``open`` field (True unless its status
    is one of done/complete/completed/closed). Dotfiles, non-files and a
    missing dir are skipped; files with no parseable line are dropped. The list
    is sorted by ``ts`` string descending, with records lacking ``ts`` last.
    """
    out: list[dict] = []
    if not checkpoints_dir.is_dir():
        return out
    for path in sorted(checkpoints_dir.iterdir()):
        if not path.is_file() or path.suffix != ".jsonl" or path.name.startswith("."):
            continue
        latest: dict | None = None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            try:
                rec = json.loads(text)
            except Exception:
                continue
            if isinstance(rec, dict):
                latest = rec
        if latest is None:
            continue
        status = str(latest.get("status", "")).strip().lower()
        latest["open"] = status not in _CLOSED_STATUSES
        out.append(latest)
    # Sort by ts string descending; records without ts go last. We sort in two
    # passes so the "missing ts last" rule is independent of the descending ts
    # order (a single reverse=True would otherwise float missing-ts to the top).
    out.sort(key=lambda r: r.get("ts") or "", reverse=True)
    out.sort(key=lambda r: r.get("ts") is None)
    return out


# --- STATUS.md head ---

def _status_head(status_path: Path) -> str | None:
    """Return the first meaningful current-state bullet line of STATUS.md."""
    if not status_path.is_file():
        return None
    try:
        lines = status_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None
    in_current = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("## 현재 상태") or stripped.lower().startswith("## current"):
            in_current = True
            continue
        if in_current:
            if stripped.startswith("- "):
                return stripped[2:].strip()
            if stripped.startswith("#"):
                break
    return None


# --- orchestration ---

def build_report(root: Path, now_epoch: float, now_iso: str,
                 max_session_age_seconds: float,
                 pointer_max_age_hours: float) -> dict:
    claims_dir = root / "agents" / "runtime" / "claims"
    sessions_dir = root / "agents" / "runtime" / "sessions"
    inbox_dir = root / "agents" / "messages" / "inbox"
    pointer_path = root / "agents" / "project" / "NEXT-SESSION-POINTER.yml"
    status_path = root / "agents" / "lead_engineer" / "STATUS.md"
    ralph_path = root / ".claude" / "ralph-loop.local.md"
    checkpoints_dir = root / "agents" / "runtime" / "checkpoints"

    stale_claims = scan_stale_claims(claims_dir, now_epoch)
    claimed_stale = scan_claimed_stale_messages(inbox_dir, claims_dir, now_epoch)
    dead_sessions = scan_dead_sessions(sessions_dir, now_epoch,
                                       max_session_age_seconds)

    pointer = check_pointer_freshness(pointer_path, now_iso, pointer_max_age_hours)
    status_head = _status_head(status_path)
    ralph = check_ralph_consistency(ralph_path, pointer, now_epoch)
    # In-flight sub-step checkpoints are normal (not anomalies): surface only the
    # OPEN ones for resume context, and never let them affect `clean`/warnings.
    open_checkpoints = [c for c in read_latest_checkpoints(checkpoints_dir)
                        if c.get("open")]

    warnings: list[str] = []
    if not pointer["exists"]:
        warnings.append("NEXT-SESSION-POINTER.yml not found")
    elif pointer["stale"]:
        age = pointer.get("age_hours")
        age_str = f"{age:.1f}" if isinstance(age, (int, float)) else "?"
        warnings.append(
            f"pointer is stale (updated {age_str}h ago, "
            f"> {pointer_max_age_hours}h)")
    warnings.extend(ralph["warnings"])
    for entry in stale_claims:
        warnings.append(f"stale claim file: {entry['file']}")
    for entry in claimed_stale:
        warnings.append(
            f"message {entry['message_id']} stuck claimed ({entry['reason']})")
    for entry in dead_sessions:
        warnings.append(
            f"candidate-abandoned session {entry['agent_id']} "
            f"(role={entry['role']}, task={entry['task_id']}, "
            f"age={entry['age_seconds']}s)")

    clean = (not warnings
             and not stale_claims
             and not claimed_stale
             and not dead_sessions)

    return {
        "resume": {
            "summary_head": pointer.get("summary_head"),
            "pointer": pointer,
            "status_head": status_head,
            "ralph": ralph,
            "checkpoints": open_checkpoints,
        },
        "crash_scan": {
            "stale_claims": stale_claims,
            "claimed_stale_messages": claimed_stale,
            "candidate_dead_sessions": dead_sessions,
        },
        "warnings": warnings,
        "clean": clean,
    }


def render_report(report: dict) -> str:
    resume = report.get("resume", {})
    pointer = resume.get("pointer", {}) if isinstance(resume, dict) else {}
    ralph = resume.get("ralph", {}) if isinstance(resume, dict) else {}
    scan = report.get("crash_scan", {})

    summary_head = resume.get("summary_head") or "(no pointer summary)"
    updated_at = pointer.get("updated_at") or "?"
    age = pointer.get("age_hours")
    age_str = f"{age:.1f}" if isinstance(age, (int, float)) else "?"
    signal = pointer.get("signal") or "?"
    score = pointer.get("score") or "?"
    status_head = resume.get("status_head") or "(no STATUS.md current-state line)"

    lines = ["=== SESSION RESUME CHECK ==="]
    lines.append(
        f"RESUME HERE: {summary_head}  (pointer updated_at={updated_at}, "
        f"age={age_str}h, signal={signal}/{score})")
    lines.append(f"  STATUS.md: {status_head}")
    lines.append(
        f"  ralph-loop: active={ralph.get('active')} "
        f"iteration={ralph.get('iteration')}")
    checkpoints = resume.get("checkpoints", []) if isinstance(resume, dict) else []
    for cp in checkpoints:
        if not isinstance(cp, dict):
            continue
        lines.append(
            f"  IN-FLIGHT: {cp.get('task', '?')} — step "
            f"'{cp.get('step', '?')}' ({cp.get('status', '?')}); next: "
            f"'{cp.get('next', '')}' @ {cp.get('ts', '?')}")
    lines.append(
        "CRASH SCAN: "
        f"stale_claims={len(scan.get('stale_claims', []))} "
        f"claimed_stale_msgs={len(scan.get('claimed_stale_messages', []))} "
        f"candidate_dead_sessions={len(scan.get('candidate_dead_sessions', []))}")

    warnings = report.get("warnings", [])
    if report.get("clean"):
        lines.append("OK: no crash-recovery anomalies; state is consistent.")
    else:
        lines.append("WARNINGS:")
        for w in warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


# --- CLI ---

def main(argv: list[str] | None = None) -> int:
    # Shared parent parser so BOTH the audit path and the checkpoint subcommand
    # accept --root identically.
    root_parent = argparse.ArgumentParser(add_help=False)
    # default=SUPPRESS so the checkpoint subparser does NOT clobber a --root
    # given before the subcommand (argparse would otherwise re-apply the
    # subparser's default and silently discard `--root X checkpoint ...`).
    # Both `--root X checkpoint ...` and `checkpoint --root X ...` now work.
    root_parent.add_argument("--root", default=argparse.SUPPRESS,
                             help="repo root (default: message_queue.REPO_ROOT)")

    parser = argparse.ArgumentParser(
        parents=[root_parent],
        description="Crash-recovery + session-resume auditor (report-only, "
                    "non-blocking; always exits 0 unless --strict).")
    # Audit-only flags live on the top-level parser.
    parser.add_argument("--json", action="store_true",
                        help="print the report dict as JSON instead of text")
    parser.add_argument("--fix", action="store_true",
                        help="recover stale claims for claimed-stale messages "
                             "(the ONLY mutating action)")
    parser.add_argument("--max-session-age-hours", type=float, default=6.0,
                        help="candidate-abandoned session age threshold (hours)")
    parser.add_argument("--pointer-max-age-hours", type=float, default=24.0,
                        help="pointer staleness threshold (hours)")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any warnings (default always exits 0 so "
                             "it never blocks a SessionStart hook)")

    # Optional subcommand. When omitted, behave EXACTLY as the audit CLI.
    sub = parser.add_subparsers(dest="command", required=False)
    cp = sub.add_parser(
        "checkpoint", parents=[root_parent],
        help="record a sub-step progress checkpoint for a long task "
             "(append-only; never runs the audit)")
    cp.add_argument("--task", required=True, help="task id (e.g. TASK-123)")
    cp.add_argument("--step", required=True,
                    help="what sub-step was just done/started")
    cp.add_argument("--status", choices=["started", "done", "blocked"],
                    default="started", help="checkpoint status")
    cp.add_argument("--next", default="", help="the next action to take")
    cp.add_argument("--agent", default="", help="agent/role recording this")

    args = parser.parse_args(argv)

    try:
        root = Path(getattr(args, "root", None) or str(mq.REPO_ROOT)).resolve()

        if getattr(args, "command", None) == "checkpoint":
            checkpoints_dir = root / "agents" / "runtime" / "checkpoints"
            path = append_checkpoint(
                checkpoints_dir,
                task=args.task,
                step=args.step,
                status=args.status,
                next_action=args.next,
                agent=args.agent,
                now_iso=_local_iso(),
            )
            print(f"checkpoint recorded: {path} (step='{args.step}', "
                  f"status={args.status})")
            return 0

        now_iso = _local_iso()
        now_epoch = mq._now_epoch()
        report = build_report(
            root,
            now_epoch=now_epoch,
            now_iso=now_iso,
            max_session_age_seconds=args.max_session_age_hours * 3600.0,
            pointer_max_age_hours=args.pointer_max_age_hours,
        )

        if args.fix:
            if root != mq.REPO_ROOT.resolve():
                print(
                    "WARNING: --fix only operates on the real repo root "
                    f"({mq.REPO_ROOT.resolve()}); skipping fix because --root "
                    f"points elsewhere ({root}).")
            else:
                _apply_fix(root, report)

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(render_report(report))

        if args.strict and report.get("warnings"):
            return 1
        return 0
    except Exception as exc:  # never crash a session start
        print(f"WARN: session_resume_check failed safely: {exc}")
        return 0


def _apply_fix(root: Path, report: dict) -> None:
    inbox_dir = root / "agents" / "messages" / "inbox"
    entries = report.get("crash_scan", {}).get("claimed_stale_messages", [])
    for entry in entries:
        msg_path = inbox_dir / entry["file"]
        try:
            changed = mq.recover_stale_claim(msg_path)
        except Exception as exc:
            print(f"  fix: {entry['file']} could not be recovered: {exc}")
            continue
        if changed:
            print(f"  fix: reset {entry['message_id']} -> open")
        else:
            print(f"  fix: {entry['message_id']} unchanged "
                  f"({entry['reason']}; recovery declined)")


def _local_iso() -> str:
    now = _dt.datetime.now(_dt.timezone.utc).astimezone()
    s = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    if len(s) >= 5 and s[-5] in "+-":
        s = s[:-2] + ":" + s[-2:]
    return s


if __name__ == "__main__":
    raise SystemExit(main())
