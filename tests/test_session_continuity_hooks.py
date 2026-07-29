"""Lifecycle hooks keep only bounded operational continuity state."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from agent_runtime import allimbot as package_allimbot
from agent_runtime import hook_runtime as package_dispatch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


COMPACT = load("compact_hook", ROOT / "scripts/session_compact_hook.py")
START = load("start_hook", ROOT / "scripts/session_start_hook.py")
DISPATCH = load("hook_runtime", ROOT / "src/agent_runtime/hook_runtime.py")


def invoke(main, argv, event):
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(event))), contextlib.redirect_stdout(out):
        assert main(argv) == 0
    return out.getvalue()


def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_compact_keeps_sessions_isolated_and_excludes_conversation(tmp_path: Path) -> None:
    root = git_repo(tmp_path)
    (root / "agents/project").mkdir(parents=True)
    (root / "agents/project/NEXT-SESSION-POINTER.yml").write_text(
        "active_task: TASK-17\nactive_task_set: set-a\n", encoding="utf-8"
    )
    claims = root / "agents/runtime/task_claims"; claims.mkdir(parents=True)
    for index in range(101):
        (claims / f"old-{index:03d}.json").write_text(json.dumps({"status":"released"}))
    (claims / "zz-active.json").write_text(json.dumps({"status":"claimed","claim_id":"C-1","task_id":"TASK-17","branch":"work/a"}))
    invoke(COMPACT.main, ["--root", str(root), "--phase", "pre-compact"], {"session_id":"one", "prompt":"secret prompt", "transcript":"secret transcript"})
    invoke(COMPACT.main, ["--root", str(root), "--phase", "pre-compact"], {"session_id":"two"})
    invoke(COMPACT.main, ["--root", str(root), "--phase", "post-compact"], {"session_id":"one"})
    directory = root / "agents/runtime/session_checkpoints"
    one, two, latest = (json.loads((directory / name).read_text()) for name in ("one.json", "two.json", "latest.json"))
    assert one["session_id"] == latest["session_id"] == "one"
    assert two["session_id"] == "two"
    assert one["active_task"] == "TASK-17" and one["active_task_set"] == "set-a"
    assert one["active_claims"] == [{"claim_id":"C-1","task_id":"TASK-17","branch":"work/a"}]
    serialized = json.dumps(one)
    assert "secret prompt" not in serialized and "secret transcript" not in serialized
    assert not list(directory.glob(".checkpoint-*"))


def test_compact_cleans_temporary_file_when_replace_fails(tmp_path: Path) -> None:
    target = tmp_path / "checkpoint.json"
    with patch.object(COMPACT.os, "replace", side_effect=OSError("disk error")):
        try:
            COMPACT.atomic_json(target, {"safe": True})
        except OSError:
            pass
    assert not list(tmp_path.glob(".checkpoint-*"))


def test_start_reads_compact_session_and_emits_bounded_safe_json(tmp_path: Path) -> None:
    root = tmp_path
    checkpoint = root / "agents/runtime/session_checkpoints"; checkpoint.mkdir(parents=True)
    (checkpoint / "sid.json").write_text(json.dumps({"session_id":"sid","active_task":"TASK-X","rebootstrap_required":True}))
    (root / "agents/lead_engineer").mkdir(parents=True)
    (root / "agents/lead_engineer/compound_log.md").write_text("## COMPOUND-42 latest lesson\n")
    calls = []
    def fake_run(root_arg, script, **kwargs):
        calls.append(script); return script + " ok"
    with patch.object(START, "run", fake_run):
        raw = invoke(START.main, ["--root", str(root)], {"source":"compact", "session_id":"sid", "prompt":"DO NOT ECHO", "transcript":"DO NOT ECHO"})
    payload = json.loads(raw)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert f"host={root}" in context and "source=compact" in context and "TASK-X" in context and "compound: count=1, latest=COMPOUND-42 latest lesson" in context
    assert "DO NOT ECHO" not in context and len(context) <= 6000
    assert calls[:2] == ["session_baseline.py", "claim_reaper_hook.py"]
    assert set(calls[2:]) == {"session_dashboard.py", "interrupted_run_detector.py", "session_resume_check.py", "update-notify"}


def test_start_scribe_summary_is_read_only_for_missing_and_fresh_projection(
    tmp_path: Path,
) -> None:
    (tmp_path / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: continuity\n"
        "sync:\n"
        "  mode: check-diff-apply\n"
        "  allow_silent_overwrite: false\n"
        "host:\n"
        "  state_adapters:\n"
        "    status: STATUS.md\n",
        encoding="utf-8",
    )
    source = tmp_path / "STATUS.md"
    source.write_text(
        "# State\n" + "".join(f"- active {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    source_mtime = source.stat().st_mtime_ns

    missing = START.scribe_summary(tmp_path)
    assert "state=overdue" in missing and "projection=missing" in missing
    projection = tmp_path / START.state_projection.DEFAULT_PROJECTION_PATH
    assert not projection.exists()
    assert source.stat().st_mtime_ns == source_mtime

    START.state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    projection_mtime = projection.stat().st_mtime_ns
    fresh = START.scribe_summary(tmp_path)
    assert "projection=fresh" in fresh and "readiness=ready" in fresh
    assert source.stat().st_mtime_ns == source_mtime
    assert projection.stat().st_mtime_ns == projection_mtime


def test_dispatcher_discovers_git_root_and_preserves_blocking_streams(tmp_path: Path) -> None:
    root = git_repo(tmp_path)
    child = root / "nested"; child.mkdir()
    calls = []
    class Result:
        returncode = 7; stdout = "stdout"; stderr = "stderr"
    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        if args[0] == "git": return subprocess.CompletedProcess(args, 0, str(root) + "\n", "")
        return Result()
    with patch.object(DISPATCH.subprocess, "run", fake_run), patch.object(sys, "stdin", io.StringIO(json.dumps({"cwd":str(child)}))), patch.object(sys, "stdout", io.StringIO()) as out, patch.object(sys, "stderr", io.StringIO()) as err:
        assert DISPATCH.main(["stop-owner"]) == 7
        assert out.getvalue() == "stdout" and err.getvalue() == "stderr"
    child_args, child_kwargs = calls[-1]
    assert child_args[-1].endswith("scripts/stop_hook_owner_governance.py")
    assert child_kwargs["input"] == json.dumps({"cwd":str(child)}) and child_kwargs["cwd"] == root


def test_dispatcher_uses_mode_specific_arguments_and_fail_open_advisories(tmp_path: Path) -> None:
    root = git_repo(tmp_path)
    captured = []
    def fake_run(args, **kwargs):
        if args[0] == "git": return subprocess.CompletedProcess(args, 0, str(root) + "\n", "")
        captured.append(args); return subprocess.CompletedProcess(args, 0, "not-json", "")
    with patch.object(DISPATCH.subprocess, "run", fake_run), patch.object(sys, "stdin", io.StringIO(json.dumps({"cwd":str(root)}))), contextlib.redirect_stdout(io.StringIO()) as out:
        assert DISPATCH.main(["session-start"]) == 0
        assert json.loads(out.getvalue())["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert captured[-1][-2:] == ["--root", str(root)]


def test_dispatcher_mode_arguments_are_allowlisted(tmp_path: Path) -> None:
    root = git_repo(tmp_path)
    captured = []
    def fake_run(args, **kwargs):
        if args[0] == "git": return subprocess.CompletedProcess(args, 0, str(root) + "\n", "")
        captured.append(args); return subprocess.CompletedProcess(args, 0, "{}", "")
    for mode in ("pre-compact", "post-compact", "prompt-submit", "posttool-owner-doc"):
        with patch.object(DISPATCH.subprocess, "run", fake_run), patch.object(sys, "stdin", io.StringIO(json.dumps({"cwd":str(root)}))), contextlib.redirect_stdout(io.StringIO()):
            assert DISPATCH.main([mode]) == 0
    assert captured[0][-4:] == ["--root", str(root), "--phase", "pre-compact"]
    assert captured[1][-4:] == ["--root", str(root), "--phase", "post-compact"]
    assert captured[2][-1].endswith("scripts/taskset_prompt_hook.py")
    assert captured[3][-2:] == ["--manifest", "owner-docs.yml"]


def test_turn_event_uses_one_portable_stop_mode_and_bounded_fields(
    tmp_path: Path, monkeypatch
) -> None:
    recipe = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / ".allimbot.json"
    )
    (tmp_path / ".allimbot.json").write_text(
        recipe.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object], Path]] = []
    monkeypatch.setattr(
        package_allimbot,
        "emit_event",
        lambda event_type, data, *, root, **_kwargs: calls.append(
            (event_type, dict(data), root)
        ),
    )

    package_dispatch._emit_turn_completed(
        "stop-owner",
        tmp_path,
        {"task_id": "TASK-1"},
        returncode=0,
        duration_seconds=1.5,
    )
    package_dispatch._emit_turn_completed(
        "stop-closure",
        tmp_path,
        {"task_id": "unsafe\nprompt-secret"},
        returncode=7,
        duration_seconds=2.5,
    )

    assert calls == [
        (
            "turn.completed",
            {
                "task_id": "unscoped",
                "result_state": "blocked",
                "duration_seconds": 2.5,
            },
            tmp_path,
        )
    ]


def test_hook_configs_cover_lifecycle_windows_and_root_only_extensions() -> None:
    for path in (ROOT / ".codex/hooks.json", ROOT / "src/agent_runtime/templates/project/.codex/hooks.json"):
        hooks = json.loads(path.read_text())["hooks"]
        assert hooks["SessionStart"][0]["matcher"] == "startup|resume|clear|compact"
        assert hooks["PreCompact"][0]["matcher"] == hooks["PostCompact"][0]["matcher"] == "manual|auto"
        for groups in hooks.values():
            for group in groups:
                for hook in group["hooks"]:
                    assert hook["commandWindows"].startswith("py -3 -m agent_runtime.hook_runtime")
                    assert hook["timeout"] > 0
                    if path == ROOT / ".codex/hooks.json" and "PostToolUse" in hooks and hook["command"].endswith(("session-start", "prompt-submit", "posttool-owner-doc")):
                        assert hook["additionalContextLimit"] > 0
    root_hooks = json.loads((ROOT / ".codex/hooks.json").read_text())["hooks"]
    assert "PostToolUse" in root_hooks
    assert any("stop-dirty" in hook["command"] for hook in root_hooks["Stop"][0]["hooks"])


def test_template_installer_uses_module_dispatcher_and_is_idempotent(tmp_path: Path) -> None:
    installer = load("install_hooks", ROOT / "src/agent_runtime/templates/project/scripts/install_hooks.py")
    settings, commands = tmp_path / "settings.json", tmp_path / "commands"
    assert installer.main(["--settings", str(settings), "--commands-dir", str(commands)]) == 0
    first = json.loads(settings.read_text())
    assert installer.main(["--settings", str(settings), "--commands-dir", str(commands)]) == 0
    assert json.loads(settings.read_text()) == first
    for event, mode in installer.HOOK_MODES.items():
        command = first["hooks"][event][0]["hooks"][0]["command"]
        assert command == f'{installer._hook_python()} -m agent_runtime.hook_runtime {mode}'


def test_checkpoint_ignore_is_packaged_template_data() -> None:
    ignore = ROOT / "src/agent_runtime/templates/project/agents/runtime/session_checkpoints/.gitignore"
    assert ignore.read_text() == "*\n!.gitignore\n"
    assert '"templates/project/**/.gitignore"' in (ROOT / "pyproject.toml").read_text()
    verifier = load("verify_wheel_dotfiles", ROOT / "scripts/verify_wheel_dotfiles.py")
    assert "agent_runtime/templates/project/agents/runtime/session_checkpoints/.gitignore" in verifier.REQUIRED_FILES


def test_shared_continuity_scripts_are_exact_template_mirrors() -> None:
    template_scripts = ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"
    for name in (
        "session_start_hook.py",
        "session_compact_hook.py",
        "session_resume_check.py",
    ):
        assert (ROOT / "scripts" / name).read_bytes() == (
            template_scripts / name
        ).read_bytes()


def test_dispatcher_rejects_empty_or_extra_mode_arguments() -> None:
    assert DISPATCH.main([]) == 2
    assert DISPATCH.main(["session-start", "unexpected"]) == 2


def test_dispatcher_times_out_advisory_child_without_blocking(tmp_path: Path) -> None:
    root = git_repo(tmp_path)

    def fake_run(args, **kwargs):
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, str(root) + "\n", "")
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])

    event = json.dumps({"cwd": str(root)})
    with (
        patch.object(DISPATCH.subprocess, "run", fake_run),
        patch.object(sys, "stdin", io.StringIO(event)),
        contextlib.redirect_stdout(io.StringIO()) as out,
    ):
        assert DISPATCH.main(["session-start"]) == 0

    payload = json.loads(out.getvalue())
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "TimeoutExpired" in context


def test_dispatcher_times_out_blocking_child_as_failure(tmp_path: Path) -> None:
    root = git_repo(tmp_path)

    def fake_run(args, **kwargs):
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, str(root) + "\n", "")
        raise subprocess.TimeoutExpired(args, kwargs["timeout"])

    event = json.dumps({"cwd": str(root)})
    with (
        patch.object(DISPATCH.subprocess, "run", fake_run),
        patch.object(sys, "stdin", io.StringIO(event)),
        contextlib.redirect_stderr(io.StringIO()) as err,
    ):
        assert DISPATCH.main(["stop-owner"]) == 1

    assert "stop-owner failed" in err.getvalue()


def test_compact_git_timeout_is_recorded_as_unknown_not_failure(tmp_path: Path) -> None:
    root = git_repo(tmp_path)
    with patch.object(
        COMPACT.subprocess,
        "run",
        side_effect=subprocess.TimeoutExpired(["git"], 2),
    ):
        invoke(
            COMPACT.main,
            ["--root", str(root), "--phase", "pre-compact"],
            {"session_id": "timeout-session"},
        )

    checkpoint = json.loads(
        (
            root
            / "agents"
            / "runtime"
            / "session_checkpoints"
            / "timeout-session.json"
        ).read_text()
    )
    assert checkpoint["git"] == {
        "branch": None,
        "head": None,
        "dirty_count": None,
    }
