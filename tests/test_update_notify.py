"""Tests for the non-blocking upstream release notice (TASK-AR-509)."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from agent_runtime import update_notify
from agent_runtime.cli import main

NOTICE_LINE = "agent-runtime update available: v0.1.8 -> v0.1.9 (run: update-plan, then update)"
REMOTE_URL = "https://github.com/example/agent_runtime.git"

LS_REMOTE_OUTPUT = "\n".join(
    [
        "1111111111111111111111111111111111111111\trefs/tags/v0.1.8",
        "2222222222222222222222222222222222222222\trefs/tags/v0.1.9",
        "3333333333333333333333333333333333333333\trefs/tags/v0.1.9^{}",
        "4444444444444444444444444444444444444444\trefs/tags/not-a-release",
        "5555555555555555555555555555555555555555\trefs/tags/v0.2",
        "6666666666666666666666666666666666666666\trefs/heads/main",
    ]
)


def _write_host_config(root: Path, *, ref: str = "v0.1.8", remote_url: str = REMOTE_URL) -> None:
    (root / "agent_runtime.yml").write_text(
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                f"  remote_url: {remote_url}",
                f"  ref: {ref}",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class _FakeRun:
    """Counting stand-in for subprocess.run returning canned ls-remote output."""

    def __init__(self, stdout: str = LS_REMOTE_OUTPUT, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode
        self.calls = 0

    def __call__(self, args, **kwargs):
        self.calls += 1
        assert args[:3] == ["git", "ls-remote", "--tags"]
        assert kwargs.get("timeout") == update_notify.LS_REMOTE_TIMEOUT_SECONDS
        assert kwargs.get("env", {}).get("GIT_TERMINAL_PROMPT") == "0"
        return subprocess.CompletedProcess(args, self.returncode, stdout=self.stdout, stderr="")


def test_newer_tag_prints_notice_once(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0] == NOTICE_LINE
    assert out.count("update available") == 1
    assert len(lines) == 2  # notice + recommended-procedure hint
    assert "update-plan" in lines[1]
    out.encode("ascii")  # notice must be plain ASCII


def test_newer_tag_sends_optional_allimbot_notice(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        update_notify.allimbot,
        "notify",
        lambda message, title="agent_runtime", **_kwargs: calls.append((message, title)) or False,
    )

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert calls == [
        (
            NOTICE_LINE + "\n" + update_notify.HINT_LINE,
            "agent_runtime update available",
        )
    ]
    assert capsys.readouterr().err == ""


def test_git_terminal_prompt_forced_to_zero_even_when_inherited(tmp_path, capsys, monkeypatch):
    """An inherited GIT_TERMINAL_PROMPT=1 must be overridden, not kept."""
    _write_host_config(tmp_path, ref="v0.1.8")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "1")
    fake_run = _FakeRun()  # its __call__ asserts env["GIT_TERMINAL_PROMPT"] == "0"
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path), "--no-cache"]) == 0
    assert fake_run.calls == 1
    # The notice proves the fake ran to completion: a failed env assertion
    # inside _FakeRun would be swallowed by the non-blocking guarantee and
    # leave stdout empty instead.
    assert capsys.readouterr().out.splitlines()[0] == NOTICE_LINE


def test_same_tag_is_silent(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.9")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_same_tag_verbose_reports_up_to_date(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.9")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())

    assert main(["update-notify", "--root", str(tmp_path), "--verbose"]) == 0

    out = capsys.readouterr().out
    assert "up to date" in out
    assert "update available" not in out


def test_pinned_ref_newer_than_remote_is_silent(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.2.0")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_branch_ref_reports_latest_tag_as_informational(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="main")
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun())

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0] == "agent-runtime latest release: v0.1.9 (pinned ref: main; run: update-plan, then update)"


def test_network_timeout_exits_zero_silently(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path)

    def raise_timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args, timeout=update_notify.LS_REMOTE_TIMEOUT_SECONDS)

    monkeypatch.setattr(update_notify.subprocess, "run", raise_timeout)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_network_timeout_verbose_notes_stderr_only(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path)

    def raise_timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args, timeout=update_notify.LS_REMOTE_TIMEOUT_SECONDS)

    monkeypatch.setattr(update_notify.subprocess, "run", raise_timeout)

    assert main(["update-notify", "--root", str(tmp_path), "--verbose"]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "update-notify" in captured.err


def test_git_failure_exit_code_is_silent_zero(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path)
    monkeypatch.setattr(update_notify.subprocess, "run", _FakeRun(stdout="", returncode=128))

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_missing_config_exits_zero_silently(tmp_path, capsys, monkeypatch):
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert fake_run.calls == 0


def test_missing_upstream_section_exits_zero_silently(tmp_path, capsys, monkeypatch):
    (tmp_path / "agent_runtime.yml").write_text(
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
        encoding="utf-8",
    )
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""
    assert fake_run.calls == 0


def test_cache_hit_avoids_subprocess_but_still_notifies(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1
    cache_file = tmp_path / ".tmp" / "update-notify-cache.json"
    assert cache_file.exists()
    cached = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cached["latest_tag"] == "v0.1.9"
    assert cached["remote_url"] == REMOTE_URL
    capsys.readouterr()

    def fail_run(args, **kwargs):
        raise AssertionError("cache hit must not spawn a subprocess")

    monkeypatch.setattr(update_notify.subprocess, "run", fail_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0] == NOTICE_LINE  # notice still printed from cache


def test_no_cache_forces_subprocess(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1
    assert main(["update-notify", "--root", str(tmp_path), "--no-cache"]) == 0
    assert fake_run.calls == 2


def test_stale_cache_refreshes_via_subprocess(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    cache_file = update_notify.cache_path(tmp_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    stale = time.time() - update_notify.CACHE_TTL_SECONDS - 60
    cache_file.write_text(
        json.dumps({"checked_at": stale, "remote_url": REMOTE_URL, "latest_tag": "v0.1.8"}),
        encoding="utf-8",
    )
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1
    assert capsys.readouterr().out.splitlines()[0] == NOTICE_LINE


def test_cache_for_other_remote_is_ignored(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    cache_file = update_notify.cache_path(tmp_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps(
            {
                "checked_at": time.time(),
                "remote_url": "https://github.com/other/agent_runtime.git",
                "latest_tag": "v9.9.9",
            }
        ),
        encoding="utf-8",
    )
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1
    assert capsys.readouterr().out.splitlines()[0] == NOTICE_LINE


def test_corrupt_cache_falls_back_to_subprocess(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path, ref="v0.1.8")
    cache_file = update_notify.cache_path(tmp_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("{not json", encoding="utf-8")
    fake_run = _FakeRun()
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1


def test_failed_lookup_is_cached_to_keep_session_start_cheap(tmp_path, capsys, monkeypatch):
    _write_host_config(tmp_path)
    fake_run = _FakeRun(stdout="", returncode=128)
    monkeypatch.setattr(update_notify.subprocess, "run", fake_run)

    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1
    assert main(["update-notify", "--root", str(tmp_path)]) == 0
    assert fake_run.calls == 1  # cached failure, no second subprocess
    captured = capsys.readouterr()
    assert captured.out == ""


def test_parse_ls_remote_tags_orders_numerically():
    output = "\n".join(
        [
            "a\trefs/tags/v0.9.0",
            "b\trefs/tags/v0.10.0",
            "c\trefs/tags/v0.10.0^{}",
            "d\trefs/tags/v0.2.1",
            "e\trefs/tags/release-1",
        ]
    )
    assert update_notify.parse_ls_remote_tags(output) == ["v0.2.1", "v0.9.0", "v0.10.0"]


def test_template_wires_session_start_update_notify_hook():
    template_root = Path(__file__).resolve().parents[1] / "src" / "agent_runtime" / "templates" / "project"
    hooks = json.loads((template_root / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    session_start = hooks["hooks"]["SessionStart"]
    commands = [hook["command"] for group in session_start for hook in group["hooks"]]
    assert commands == ["python3 -m agent_runtime.hook_runtime session-start"]
    start = (template_root / "scripts" / "session_start_hook.py").read_text(encoding="utf-8")
    assert '"-m","agent_runtime.cli","update-notify"' in start
