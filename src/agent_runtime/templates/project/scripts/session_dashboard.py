"""Session-start W0 dashboard: one compact panel of the 500-series observability.

Nothing surfaced the AR-50x observability at session start, so each session
re-discovered active claims, in-flight branch divergence, upstream updates, and
SCM hygiene by hand. This wires a single fast read-only panel into SessionStart.

Sections (each degrades to a one-line note, never raises):
- W0: active claims + worktree count + in-flight divergence summary
  (reuses ``work.status_work`` so the claim/worktree/inflight git work happens
  once, not three times). Generated hosts do not ship repository-only
  ``work.py``, so a bounded, read-only fallback scans claim JSON and invokes
  the shipped ``inflight_overlay.py`` without importing its module.
- update: the non-blocking upstream release notice (``run_update_notify``);
  silent when up to date or no host config.
- scm: headline hygiene counts (zombies / stale claims / unregistered issues)
  from ``scm_steward report`` -- the headline only, not the full report.

Guarantees:
- always exit 0 (never blocks a session start);
- cp949-safe (ASCII only on the human path, ensure_ascii JSON);
- a hard timeout on every dashboard-owned subprocess so a hang cannot block
  the session start; any failing section degrades to a note. On the fallback
  path, two W0 reads run before update_notify's ls-remote (10s internal cap)
  and the scm subprocess (``SCM_TIMEOUT_SECONDS``), so the SessionStart hook's
  outer timeout must exceed their serial sum plus startup (wired at 35s) or
  the runner preempts the process and voids the always-exit-0 guarantee;
- ``--json`` for machine use; ``--quiet`` suppresses the panel when clean.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SCHEMA = "agent-runtime-session-dashboard/v1"
SCM_TIMEOUT_SECONDS = 10.0
W0_FALLBACK_TIMEOUT_SECONDS = 5.0
ACTIVE_CLAIM_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}


def _ascii(value: Any) -> str:
    """cp949-safe rendering: drop anything outside ASCII to a placeholder."""
    return str(value if value is not None else "").encode("ascii", "replace").decode("ascii")


# ---------------------------------------------------------------------------
# Section builders -- each returns a dict and NEVER raises.
# ---------------------------------------------------------------------------


def _active_claim_count(root: Path) -> tuple[int, list[str]]:
    """Count active claim JSON records without requiring repository modules."""
    claims_dir = root / "agents" / "runtime" / "task_claims"
    if not claims_dir.is_dir():
        return 0, []

    count = 0
    notes: list[str] = []
    try:
        paths = sorted(claims_dir.glob("*.json"), key=lambda path: path.name.lower())
    except OSError as exc:
        return 0, [f"claim scan unavailable: {_ascii(exc.__class__.__name__)}"]
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            notes.append(
                f"claim ignored: {_ascii(path.name)} ({_ascii(exc.__class__.__name__)})"
            )
            continue
        if not isinstance(payload, dict):
            notes.append(f"claim ignored: {_ascii(path.name)} (invalid payload)")
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status in ACTIVE_CLAIM_STATUSES:
            count += 1
    return count, notes


def _parse_git_worktrees(output: str) -> list[dict[str, str]]:
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[len("worktree "):], "branch": ""}
        elif line.startswith("branch ") and current:
            branch = line[len("branch "):]
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
            current["branch"] = branch
        elif line == "detached" and current:
            current["branch"] = "(detached)"
    if current:
        worktrees.append(current)
    return worktrees


def _fallback_worktrees(
    root: Path, timeout: float
) -> tuple[list[dict[str, str]] | None, str | None]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"worktree scan timed out (>{timeout:g}s)"
    except (OSError, FileNotFoundError) as exc:
        return None, f"worktree scan unavailable: {_ascii(exc.__class__.__name__)}"
    if proc.returncode != 0:
        return None, "worktree scan unavailable: git returned non-zero"
    return _parse_git_worktrees(proc.stdout), None


def _validated_inflight_counts(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, int] = {}
    for key in (
        "divergent_tasks",
        "divergent_records",
        "branches_with_divergence",
        "claimless",
    ):
        raw = value.get(key, 0)
        if isinstance(raw, bool):
            return None
        try:
            count = int(raw)
        except (TypeError, ValueError, OverflowError):
            return None
        if count < 0 or (isinstance(raw, float) and raw != count):
            return None
        normalized[key] = count
    return normalized


def _fallback_inflight(root: Path, timeout: float) -> tuple[str, dict[str, Any], str | None]:
    script = SCRIPTS_DIR / "inflight_overlay.py"
    unavailable = "inflight: unavailable"
    if not script.is_file():
        return unavailable, {}, "inflight scan unavailable: script missing"
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--root", str(root), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return unavailable, {}, f"inflight scan timed out (>{timeout:g}s)"
    except (OSError, FileNotFoundError) as exc:
        return unavailable, {}, f"inflight scan unavailable: {_ascii(exc.__class__.__name__)}"
    if proc.returncode != 0:
        return unavailable, {}, "inflight scan unavailable: subprocess returned non-zero"
    try:
        overlay = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return unavailable, {}, "inflight scan unavailable: invalid JSON"
    if not isinstance(overlay, dict):
        return unavailable, {}, "inflight scan unavailable: invalid payload"

    raw_counts = overlay.get("summary")
    if overlay.get("error"):
        note = f"inflight scan unavailable: {_ascii(overlay.get('error'))}"
        counts = _validated_inflight_counts(raw_counts) or {}
        return f"inflight: unavailable ({_ascii(overlay.get('error'))})", counts, note
    counts = _validated_inflight_counts(raw_counts)
    if counts is None:
        return unavailable, {}, "inflight scan unavailable: invalid count payload"
    summary = (
        f"inflight: {counts.get('divergent_tasks', 0)} tasks diverge "
        f"across {counts.get('branches_with_divergence', 0)} branches"
    )
    claimless = int(counts.get("claimless") or 0)
    if claimless:
        summary += f" ({claimless} claimless)"
    return summary, counts, None


def _fallback_w0_section(
    root: Path,
    *,
    cause: Exception,
    timeout: float = W0_FALLBACK_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Build structured W0 data using only read-only host-visible assets."""
    fallback_reason = f"repository work API unavailable: {_ascii(cause.__class__.__name__)}"
    notes: list[str] = []
    try:
        claims, claim_notes = _active_claim_count(root)
    except Exception as exc:
        claims, claim_notes = 0, [f"claim scan unexpected {_ascii(exc.__class__.__name__)}"]
    notes.extend(claim_notes)
    try:
        worktrees, worktree_note = _fallback_worktrees(root, timeout)
    except Exception as exc:
        worktrees = None
        worktree_note = f"worktree scan unexpected {_ascii(exc.__class__.__name__)}"
    if worktree_note:
        notes.append(worktree_note)
    try:
        inflight_summary, inflight_counts, inflight_note = _fallback_inflight(root, timeout)
    except Exception as exc:
        inflight_summary, inflight_counts = "inflight: unavailable", {}
        inflight_note = f"inflight scan unexpected {_ascii(exc.__class__.__name__)}"
    if inflight_note:
        notes.append(inflight_note)
    return {
        "status": "ok",
        "source": "fallback",
        "fallback_reason": fallback_reason,
        "active_claims": claims,
        "worktrees": len(worktrees) if worktrees is not None else None,
        "inflight_summary": _ascii(inflight_summary),
        "inflight_counts": inflight_counts,
        "notes": notes,
    }


def build_w0_section(root: Path) -> dict[str, Any]:
    """Active claims + worktrees + in-flight divergence in a single git pass."""
    try:
        import work  # heavy import; isolated here so a missing work.py degrades

        status = work.status_work(root)
        claims = status.get("active_claims") or []
        worktrees = status.get("worktrees")
        worktree_count = len(worktrees) if isinstance(worktrees, list) else None
        inflight = status.get("inflight") or {}
        return {
            "status": "ok",
            "source": "work",
            "active_claims": len(claims),
            "worktrees": worktree_count,
            "inflight_summary": _ascii(inflight.get("summary") or "inflight: unavailable"),
            "inflight_counts": inflight.get("counts") or {},
            "notes": [],
        }
    except Exception as exc:
        try:
            return _fallback_w0_section(root, cause=exc)
        except Exception as fallback_exc:
            note = f"w0 fallback unavailable: {_ascii(fallback_exc.__class__.__name__)}"
            return {
                "status": "error",
                "source": "fallback",
                "active_claims": 0,
                "worktrees": None,
                "inflight_summary": "inflight: unavailable",
                "inflight_counts": {},
                "notes": [note],
                "note": note,
            }


def build_update_section(root: Path) -> dict[str, Any]:
    """Capture the non-blocking upstream release notice (silent when current)."""
    try:
        from agent_runtime.update_notify import run_update_notify

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            run_update_notify(root)
        lines = [_ascii(line) for line in buffer.getvalue().splitlines() if line.strip()]
        return {"status": "ok", "lines": lines}
    except Exception as exc:
        return {"status": "error", "note": f"update check unavailable: {_ascii(exc.__class__.__name__)}"}


def _scm_command(root: Path) -> list[str]:
    return [
        sys.executable,
        str(SCRIPTS_DIR / "scm_steward.py"),
        "report",
        "--root",
        str(root),
        "--json",
    ]


def build_scm_section(root: Path, *, timeout: float = SCM_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Headline SCM hygiene counts via a timeout-bounded ``scm_steward report``.

    Run as a subprocess (not an import) so the gh/git network calls inside the
    report are bounded by a hard timeout: a credential prompt or offline remote
    can never block a session start.
    """
    try:
        proc = subprocess.run(
            _scm_command(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "note": f"scm hygiene check timed out (>{int(timeout)}s)"}
    except Exception as exc:
        return {"status": "error", "note": f"scm hygiene unavailable: {_ascii(exc.__class__.__name__)}"}

    if proc.returncode != 0:
        return {"status": "error", "note": "scm hygiene check failed (non-zero exit)"}
    try:
        report = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "error", "note": "scm hygiene check produced no parseable report"}

    sections = report.get("sections") or {}
    worktrees = (sections.get("worktrees") or {}).get("counts") or {}
    claims = (sections.get("claims") or {}).get("counts") or {}
    github = (sections.get("github") or {}).get("counts") or {}
    github_status = (sections.get("github") or {}).get("status") or "ok"
    counts = {
        "zombies": int(worktrees.get("zombies") or 0),
        "stale_claims": int(claims.get("stale") or 0),
        "unregistered_issues": int(github.get("unregistered") or 0),
    }
    # gh may be unavailable (offline/no auth); the issue count is then unknown
    # rather than zero, so flag it instead of silently reporting clean.
    issues_known = github_status not in {"unavailable", "error"}
    return {"status": "ok", "counts": counts, "issues_known": issues_known}


def build_dashboard(root: Path | str, *, scm_timeout: float = SCM_TIMEOUT_SECONDS) -> dict[str, Any]:
    root_path = Path(root).resolve()
    return {
        "schema": SCHEMA,
        "root": str(root_path),
        "w0": build_w0_section(root_path),
        "update": build_update_section(root_path),
        "scm": build_scm_section(root_path, timeout=scm_timeout),
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _w0_line(w0: dict[str, Any]) -> str:
    if w0.get("status") != "ok":
        return f"W0  | {_ascii(w0.get('note') or 'unavailable')}"
    worktrees = w0.get("worktrees")
    worktree_text = "n/a" if worktrees is None else str(worktrees)
    line = (
        f"W0  | claims={w0.get('active_claims', 0)} "
        f"worktrees={worktree_text} | {_ascii(w0.get('inflight_summary'))}"
    )
    notes = w0.get("notes") or []
    if notes:
        line += f" | notes={'; '.join(_ascii(note) for note in notes)}"
    return line


def _scm_line(scm: dict[str, Any]) -> str:
    if scm.get("status") != "ok":
        return f"SCM | {_ascii(scm.get('note') or 'unavailable')}"
    counts = scm.get("counts") or {}
    issues = counts.get("unregistered_issues", 0)
    issues_text = str(issues) if scm.get("issues_known", True) else "?"
    return (
        f"SCM | zombies={counts.get('zombies', 0)} "
        f"stale_claims={counts.get('stale_claims', 0)} "
        f"unregistered_issues={issues_text}"
    )


def is_clean(dashboard: dict[str, Any]) -> bool:
    """True when nothing needs attention and no section errored."""
    w0 = dashboard.get("w0") or {}
    update = dashboard.get("update") or {}
    scm = dashboard.get("scm") or {}
    if w0.get("status") != "ok" or update.get("status") != "ok" or scm.get("status") != "ok":
        return False
    if w0.get("notes"):
        return False
    if update.get("lines"):
        return False
    counts = w0.get("inflight_counts") or {}
    if int(counts.get("divergent_tasks") or 0) or int(w0.get("active_claims") or 0):
        return False
    scm_counts = scm.get("counts") or {}
    if any(int(value or 0) for value in scm_counts.values()):
        return False
    return True


def render_panel(dashboard: dict[str, Any]) -> str:
    lines = ["=== session dashboard (W0) ==="]
    lines.append(_w0_line(dashboard.get("w0") or {}))
    update = dashboard.get("update") or {}
    if update.get("status") != "ok":
        lines.append(f"UPD | {_ascii(update.get('note') or 'unavailable')}")
    else:
        update_lines = update.get("lines") or []
        if update_lines:
            for index, text in enumerate(update_lines):
                prefix = "UPD |" if index == 0 else "    |"
                lines.append(f"{prefix} {text}")
        else:
            lines.append("UPD | up to date")
    lines.append(_scm_line(dashboard.get("scm") or {}))
    lines.append("=" * 31)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="One-call session-start W0 dashboard (claims/worktrees/inflight + update + scm hygiene)."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--quiet", action="store_true", help="suppress output when everything is clean")
    parser.add_argument(
        "--scm-timeout",
        type=float,
        default=SCM_TIMEOUT_SECONDS,
        help=f"hard timeout (s) for the scm hygiene subprocess (default: {int(SCM_TIMEOUT_SECONDS)})",
    )
    args = parser.parse_args(argv)

    dashboard = build_dashboard(args.root, scm_timeout=args.scm_timeout)
    if args.quiet and is_clean(dashboard):
        return 0
    if args.json:
        print(json.dumps(dashboard, ensure_ascii=True, indent=2))
    else:
        print(render_panel(dashboard))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
