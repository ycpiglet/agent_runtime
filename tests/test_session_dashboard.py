"""Tests for the session-start W0 dashboard (TASK-AR-523).

Covers: panel contains the W0/update/scm sections; --json shape; exit 0 even
when a section errors (failing scm subprocess injected); --quiet suppresses
clean output; hook wiring present in both .codex/hooks.json copies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import session_dashboard

SCRIPT = REPO_ROOT / "scripts" / "session_dashboard.py"
TEMPLATE_SCRIPT = (
    REPO_ROOT
    / "src"
    / "agent_runtime"
    / "templates"
    / "project"
    / "scripts"
    / "session_dashboard.py"
)
TEMPLATE_INFLIGHT = TEMPLATE_SCRIPT.with_name("inflight_overlay.py")


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


def test_w0_prefers_richer_repository_work_path(monkeypatch: pytest.MonkeyPatch) -> None:
    import work

    monkeypatch.setattr(
        work,
        "status_work",
        lambda root: {
            "active_claims": [{"claim_id": "CLAIM-root"}],
            "worktrees": [{"path": str(root), "branch": "main"}],
            "inflight": {
                "summary": "inflight: 0 tasks diverge across 0 branches",
                "counts": {"divergent_tasks": 0, "branches_with_divergence": 0},
            },
        },
    )

    section = session_dashboard.build_w0_section(REPO_ROOT)

    assert section["status"] == "ok"
    assert section["source"] == "work"
    assert section["active_claims"] == 1
    assert section["worktrees"] == 1
    assert section["notes"] == []


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


def test_w0_fallback_partial_failures_remain_explicit_notes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(session_dashboard, "SCRIPTS_DIR", tmp_path / "missing-scripts")

    section = session_dashboard._fallback_w0_section(
        tmp_path / "not-a-repository",
        cause=ModuleNotFoundError("work"),
        timeout=0.1,
    )

    assert section["status"] == "ok"
    assert section["source"] == "fallback"
    assert section["active_claims"] == 0
    assert section["worktrees"] is None
    assert section["inflight_summary"] == "inflight: unavailable"
    assert "work API unavailable" in section["fallback_reason"]
    assert any("worktree scan unavailable" in note for note in section["notes"])
    assert any("script missing" in note for note in section["notes"])
    assert session_dashboard.is_clean(
        {
            "w0": section,
            "update": {"status": "ok", "lines": []},
            "scm": {"status": "ok", "counts": {}},
        }
    ) is False


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


def test_clean_template_without_work_py_uses_read_only_w0_fallback(tmp_path: Path) -> None:
    """A generated host must not need the repository-only scripts/work.py."""
    host = tmp_path / "host"
    scripts = host / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(TEMPLATE_SCRIPT, scripts / "session_dashboard.py")
    shutil.copy2(TEMPLATE_INFLIGHT, scripts / "inflight_overlay.py")
    assert not (scripts / "work.py").exists()

    subprocess.run(["git", "init", "-b", "main", str(host)], check=True, capture_output=True)
    (host / "README.md").write_text("clean host\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(host), "add", "."], check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(host),
            "-c",
            "user.name=Agent Runtime Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "initialize clean host",
        ],
        check=True,
        capture_output=True,
    )
    claims = host / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True)
    (claims / "CLAIM-clean-host.json").write_text(
        json.dumps(
            {
                "claim_id": "CLAIM-clean-host",
                "task_id": "TASK-HOST-001",
                "task_set_id": "TASKSET-HOST-W0",
                "status": "in_progress",
                "agent_instance_id": "host-worker",
            }
        ),
        encoding="utf-8",
    )
    before = {
        path.relative_to(host): path.read_bytes()
        for path in host.rglob("*")
        if path.is_file()
    }

    proc = subprocess.run(
        [
            sys.executable,
            str(scripts / "session_dashboard.py"),
            "--root",
            str(host),
            "--json",
            "--scm-timeout",
            "0.1",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["w0"]["status"] == "ok"
    assert payload["w0"]["source"] == "fallback"
    assert payload["w0"]["active_claims"] == 1
    assert payload["w0"]["worktrees"] == 1
    assert payload["w0"]["inflight_counts"]["divergent_tasks"] == 0
    assert "work API unavailable" in payload["w0"]["fallback_reason"]
    assert payload["w0"]["notes"] == []
    after = {
        path.relative_to(host): path.read_bytes()
        for path in host.rglob("*")
        if path.is_file()
    }
    assert after == before


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


def _session_start_hooks(hooks_path: Path) -> list[dict]:
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    hooks: list[dict] = []
    for group in data["hooks"]["SessionStart"]:
        hooks.extend(group["hooks"])
    return hooks


def _session_start_commands(hooks_path: Path) -> list[str]:
    return [hook["command"] for hook in _session_start_hooks(hooks_path)]


# Worst case the generated-host fallback waits on two serial W0 subprocesses,
# then two serial network-aware operations (update_notify + scm_steward). The
# outer hook timeout must exceed their sum plus startup, or the runner preempts
# the process and the always-exit-0 guarantee is voided.
_MIN_DASHBOARD_HOOK_TIMEOUT = (
    (2 * int(session_dashboard.W0_FALLBACK_TIMEOUT_SECONDS))
    + int(session_dashboard.SCM_TIMEOUT_SECONDS)
    + 10  # update_notify ls-remote
)


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


@pytest.mark.parametrize(
    "hooks_path",
    [
        REPO_ROOT / ".codex" / "hooks.json",
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / ".codex" / "hooks.json",
    ],
)
def test_dashboard_hook_timeout_exceeds_internal_network_budget(hooks_path: Path) -> None:
    dashboard_hooks = [
        hook for hook in _session_start_hooks(hooks_path) if "session_dashboard.py" in hook["command"]
    ]
    assert dashboard_hooks, f"no session_dashboard hook in {hooks_path}"
    for hook in dashboard_hooks:
        assert hook["timeout"] > _MIN_DASHBOARD_HOOK_TIMEOUT, (
            f"hook timeout {hook['timeout']} must exceed worst-case serial "
            f"network budget {_MIN_DASHBOARD_HOOK_TIMEOUT}s in {hooks_path}"
        )


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
