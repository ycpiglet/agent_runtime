"""Tests for the session-start W0 dashboard (TASK-AR-523).

Covers: panel contains the W0/update/scm sections; --json shape; exit 0 even
when a section errors (failing scm subprocess injected); --quiet suppresses
clean output; hook wiring present in both .codex/hooks.json copies.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import session_dashboard

SCRIPT = REPO_ROOT / "scripts" / "session_dashboard.py"


# ---------------------------------------------------------------------------
# Section stubs: keep tests fast and deterministic (no real git/gh/network).
# ---------------------------------------------------------------------------


def _stub_sections(
    monkeypatch: pytest.MonkeyPatch,
    *,
    w0: dict | None = None,
    update: dict | None = None,
    scm: dict | None = None,
) -> None:
    monkeypatch.setattr(
        session_dashboard,
        "build_w0_section",
        lambda root: w0
        if w0 is not None
        else {
            "status": "ok",
            "active_claims": 2,
            "worktrees": 3,
            "inflight_summary": "inflight: 1 tasks diverge across 1 branches",
            "inflight_counts": {"divergent_tasks": 1},
        },
    )
    monkeypatch.setattr(
        session_dashboard,
        "build_update_section",
        lambda root: update if update is not None else {"status": "ok", "lines": []},
    )
    monkeypatch.setattr(
        session_dashboard,
        "build_scm_section",
        lambda root, timeout=session_dashboard.SCM_TIMEOUT_SECONDS: scm
        if scm is not None
        else {
            "status": "ok",
            "counts": {"zombies": 1, "stale_claims": 2, "unregistered_issues": 3},
            "issues_known": True,
        },
    )


# ---------------------------------------------------------------------------
# Panel structure
# ---------------------------------------------------------------------------


def test_panel_contains_all_three_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_sections(monkeypatch)
    dashboard = session_dashboard.build_dashboard(REPO_ROOT)
    panel = session_dashboard.render_panel(dashboard)
    assert "W0  |" in panel
    assert "UPD |" in panel
    assert "SCM |" in panel
    # headline counts surface on the W0 and SCM lines
    assert "claims=2" in panel
    assert "worktrees=3" in panel
    assert "inflight:" in panel
    assert "zombies=1" in panel
    assert "stale_claims=2" in panel
    assert "unregistered_issues=3" in panel


def test_update_lines_render_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    notice = "agent-runtime update available: v0.1.8 -> v0.1.9 (run: update-plan, then update)"
    _stub_sections(monkeypatch, update={"status": "ok", "lines": [notice, "hint: bump upstream.ref"]})
    panel = session_dashboard.render_panel(session_dashboard.build_dashboard(REPO_ROOT))
    assert notice in panel
    assert "hint: bump upstream.ref" in panel


def test_panel_is_ascii_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_sections(
        monkeypatch,
        w0={
            "status": "ok",
            "active_claims": 1,
            "worktrees": 1,
            "inflight_summary": "inflight: 진행",  # non-ASCII Korean
            "inflight_counts": {},
        },
    )
    panel = session_dashboard.render_panel(session_dashboard.build_dashboard(REPO_ROOT))
    panel.encode("cp949")  # must not raise: cp949-safe
    panel.encode("ascii")  # human path is pure ASCII


# ---------------------------------------------------------------------------
# --json shape
# ---------------------------------------------------------------------------


def test_json_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_sections(monkeypatch)
    dashboard = session_dashboard.build_dashboard(REPO_ROOT)
    assert dashboard["schema"] == session_dashboard.SCHEMA
    for key in ("w0", "update", "scm"):
        assert key in dashboard
    assert dashboard["scm"]["counts"] == {
        "zombies": 1,
        "stale_claims": 2,
        "unregistered_issues": 3,
    }
    # JSON must be cp949-safe (ensure_ascii)
    json.dumps(dashboard, ensure_ascii=True)


# ---------------------------------------------------------------------------
# Exit 0 / degradation when a section errors
# ---------------------------------------------------------------------------


def test_scm_subprocess_failure_degrades_to_note(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*args, **kwargs):
        raise OSError("git not found")

    monkeypatch.setattr(session_dashboard.subprocess, "run", _boom)
    section = session_dashboard.build_scm_section(REPO_ROOT)
    assert section["status"] == "error"
    assert "scm hygiene unavailable" in section["note"]


def test_scm_subprocess_timeout_degrades_to_note(monkeypatch: pytest.MonkeyPatch) -> None:
    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="scm_steward", timeout=10)

    monkeypatch.setattr(session_dashboard.subprocess, "run", _timeout)
    section = session_dashboard.build_scm_section(REPO_ROOT, timeout=10)
    assert section["status"] == "timeout"
    assert "timed out" in section["note"]


def test_main_exits_zero_when_scm_section_errors(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _stub_sections(monkeypatch, scm={"status": "error", "note": "scm hygiene unavailable: OSError"})
    rc = session_dashboard.main(["--root", str(REPO_ROOT)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SCM | scm hygiene unavailable: OSError" in out
    assert "W0  |" in out  # other sections still render


def test_real_run_exits_zero_and_prints_panel() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT), "--scm-timeout", "30"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0
    assert "session dashboard" in proc.stdout
    proc.stdout.encode("cp949")  # cp949-safe end to end


# ---------------------------------------------------------------------------
# --quiet
# ---------------------------------------------------------------------------


def test_is_clean_true_when_nothing_to_report(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_sections(
        monkeypatch,
        w0={
            "status": "ok",
            "active_claims": 0,
            "worktrees": 0,
            "inflight_summary": "inflight: 0 tasks diverge across 0 branches",
            "inflight_counts": {"divergent_tasks": 0},
        },
        update={"status": "ok", "lines": []},
        scm={
            "status": "ok",
            "counts": {"zombies": 0, "stale_claims": 0, "unregistered_issues": 0},
            "issues_known": True,
        },
    )
    dashboard = session_dashboard.build_dashboard(REPO_ROOT)
    assert session_dashboard.is_clean(dashboard) is True


def test_quiet_suppresses_clean_output(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _stub_sections(
        monkeypatch,
        w0={
            "status": "ok",
            "active_claims": 0,
            "worktrees": 0,
            "inflight_summary": "inflight: 0 tasks diverge across 0 branches",
            "inflight_counts": {"divergent_tasks": 0},
        },
        update={"status": "ok", "lines": []},
        scm={
            "status": "ok",
            "counts": {"zombies": 0, "stale_claims": 0, "unregistered_issues": 0},
            "issues_known": True,
        },
    )
    rc = session_dashboard.main(["--root", str(REPO_ROOT), "--quiet"])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_quiet_still_prints_when_not_clean(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _stub_sections(monkeypatch)  # defaults have claims + scm counts -> not clean
    rc = session_dashboard.main(["--root", str(REPO_ROOT), "--quiet"])
    assert rc == 0
    assert "session dashboard" in capsys.readouterr().out


def test_is_clean_false_when_section_errored(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_sections(monkeypatch, scm={"status": "timeout", "note": "scm hygiene check timed out"})
    dashboard = session_dashboard.build_dashboard(REPO_ROOT)
    assert session_dashboard.is_clean(dashboard) is False


# ---------------------------------------------------------------------------
# Hook wiring present in both .codex/hooks.json copies
# ---------------------------------------------------------------------------


def _session_start_commands(hooks_path: Path) -> list[str]:
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    commands: list[str] = []
    for group in data["hooks"]["SessionStart"]:
        for hook in group["hooks"]:
            commands.append(hook["command"])
    return commands


def test_main_hooks_json_wires_dashboard_after_baseline() -> None:
    commands = _session_start_commands(REPO_ROOT / ".codex" / "hooks.json")
    assert any("session_dashboard.py" in cmd for cmd in commands)
    assert any("session_baseline.py" in cmd for cmd in commands)
    # dashboard runs AFTER session_baseline (do not remove baseline)
    baseline_idx = next(i for i, cmd in enumerate(commands) if "session_baseline.py" in cmd)
    dashboard_idx = next(i for i, cmd in enumerate(commands) if "session_dashboard.py" in cmd)
    assert dashboard_idx > baseline_idx


def test_template_hooks_json_wires_dashboard() -> None:
    template_hooks = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / ".codex" / "hooks.json"
    )
    commands = _session_start_commands(template_hooks)
    assert any("session_dashboard.py" in cmd for cmd in commands)


def test_template_script_is_byte_identical_mirror() -> None:
    canonical = (REPO_ROOT / "scripts" / "session_dashboard.py").read_bytes()
    template = (
        REPO_ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "session_dashboard.py"
    ).read_bytes()
    assert canonical == template
