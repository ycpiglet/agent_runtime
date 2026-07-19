"""Smoke coverage for the shipped session_resume_check (issue #274 part 2).

Host-proven on autofolio (crash-recovery hardening, autofolio #121); upstreamed
so every consumer gets the SessionStart crash-recovery UX. Safety contract:
the check must NEVER break a session start — always exit 0 without --strict.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "session_resume_check.py"
)


def _run(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *extra],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_empty_root_exits_zero_with_resume_block(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "RESUME HERE" in result.stdout
    assert "CRASH SCAN" in result.stdout


def test_pointer_summary_is_surfaced(tmp_path: Path) -> None:
    pointer = tmp_path / "agents" / "project" / "NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(
        "updated_at: 2026-07-06T10:00:00+09:00\n"
        "current_state:\n"
        "  signal: green\n"
        "  summary: >\n"
        "    resume the widget refactor\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "resume the widget refactor" in result.stdout


def test_malformed_inputs_never_break_session_start(tmp_path: Path) -> None:
    # Safety contract: garbage state prints warnings but still exits 0.
    pointer = tmp_path / "agents" / "project" / "NEXT-SESSION-POINTER.yml"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("::: not yaml :::", encoding="utf-8")
    claims = tmp_path / "agents" / "runtime" / "claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / "CLAIM-broken.claim").write_text("{half-written", encoding="utf-8")
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "stale claim file: CLAIM-broken.claim" in result.stdout


def test_json_mode_emits_parseable_report(tmp_path: Path) -> None:
    result = _run(tmp_path, "--json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "warnings" in payload or "resume" in payload or payload


def test_sessionstart_hook_chain_wires_resume_check() -> None:
    hooks = json.loads(
        (REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / ".codex" / "hooks.json")
        .read_text(encoding="utf-8")
    )
    session_start = hooks["hooks"]["SessionStart"][0]["hooks"]
    commands = [entry["command"] for entry in session_start]
    assert commands[:5] == [
        "scripts\\update_notify_hook.cmd",
        "python scripts/session_dashboard.py --root .",
        "python scripts/claim_reaper_hook.py --root .",
        "python scripts/interrupted_run_detector.py --root .",
        "python scripts/session_resume_check.py --root .",
    ]
