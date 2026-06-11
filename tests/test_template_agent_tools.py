from __future__ import annotations

import importlib.util
import random
import uuid
from pathlib import Path
from subprocess import CompletedProcess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_TOOLS = REPO_ROOT / "src/agent_runtime/templates/project/scripts/providers/agent_tools.py"


def _load_agent_tools_module():
    spec = importlib.util.spec_from_file_location(
        f"agent_tools_test_{uuid.uuid4().hex}",
        AGENT_TOOLS,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _deny_subprocess(subprocess_calls):
    def _run(*_args, **_kwargs):
        subprocess_calls.append(_args)
        return CompletedProcess(args=_args[0], returncode=0, stdout="ok", stderr="")

    return _run


def _seeded_fuzz_injection_candidates(seed: int) -> set[str]:
    rng = random.Random(seed)
    base = [
        "python scripts/check_messages.py && python scripts/check_agent_docs.py",
        "python scripts/check_messages.py | python scripts/check_agent_docs.py",
        "python scripts/check_messages.py ; python scripts/check_agent_docs.py",
    ]
    replacements = {
        "&&": ["&&", "%26%26", "%2526%2526", "\\u0026\\u0026", "%u0026%u0026"],
        "|": ["|", "%7C", "%257C", "\\u007C", "%u007C"],
        ";": [";", "%3B", "%253B", "\\u003B", "%u003B"],
    }
    suffixes = [
        "",
        " %0Aecho ok",
        " %250Apython scripts/check_messages.py",
        " $%28echo%20ok%29",
    ]

    out: set[str] = set()
    for _ in range(18):
        command = rng.choice(base)
        for token, candidates in replacements.items():
            if token in command and rng.choice([True, False]):
                command = command.replace(token, rng.choice(candidates), 1)
        if rng.random() < 0.55:
            command += rng.choice(suffixes)
        if rng.random() < 0.25:
            command = command.replace("scripts/check_messages.py", "%73cripts/check_messages.py", 1)
        if rng.random() < 0.25:
            command = command.replace(" ", "%20", 1)
        out.add(command)
    return out


def test_run_command_blocks_dangerous_python_and_git(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(Path("C:/tmp"))
    blocked = [
        "python -c \"print(1)\"",
        "py -c \"print(1)\"",
        "python -m pip install requests",
        "git commit -am test",
        "git checkout .",
        "git restore --staged file.txt",
        "python - <<'PY'\nprint(1)\nPY",
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR:"), out
        assert out.startswith("ERROR"), out
        assert "profile='ci'" in out
        assert "Allowed for profile='ci'" in out
    assert calls == []


def test_run_command_allows_strict_profiles(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    allowed = [
        "python -m pytest -q",
        "python -m pytest --maxfail 1 tests/test_template_smoke.py",
        "python scripts/check_agent_docs.py",
        "python scripts/check_messages.py",
        "python scripts/agent_orchestrator.py status --json",
        "git status",
        "git diff",
        "git rev-parse HEAD",
    ]

    for command in allowed:
        out = runner.run_command(command)
        assert out.startswith("[exit 0]"), out

    # ensure each command path goes through real subprocess.run; this means parsing +
    # allowlist passed and would have blocked if violated.
    assert len(calls) == len(allowed), (len(calls), len(allowed))


def test_run_command_blocks_prompt_injection_patterns(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        "python scripts/check_messages.py && python scripts/check_agent_docs.py",
        "python scripts/check_messages.py || python scripts/check_agent_docs.py",
        "python scripts/check_messages.py | python scripts/check_agent_docs.py",
        "python scripts/check_messages.py > /tmp/messages.txt",
        "python scripts/check_messages.py < /tmp/messages.txt",
        "python scripts/check_messages.py; cat /tmp/messages.txt",
    ]

    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR: forbidden command token"), out
        assert out.startswith("ERROR: forbidden"), out
        assert "profile='ci'" in out
    assert calls == []


def test_run_command_blocks_additional_encoding_and_token_injection_patterns(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        "python scripts/check_messages.py `echo hacked`",
        "python scripts/check_messages.py $ENV:TEMP",
        "python scripts/check_messages.py $(echo hacked)",
        "python -m pytest `tests/test_template_smoke.py",
        "python scripts/agent_orchestrator.py --help; python scripts/check_messages.py",
        "python scripts/check_messages.py %COMSPEC%",
        "python scripts/check_messages.py !TEMP!",
        "python scripts/check_messages.py $env:TEMP",
        "python scripts/check_messages.py @((Get-Location).Path)",
        "python scripts/check_messages.py hello^world",
        "python scripts/check_messages.py ${PATH}info",
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "Allowed for profile='ci'" in out

    assert calls == []


def test_run_command_blocks_percent_encoded_and_here_string_variants(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        "python scripts/check_messages.py %0A",
        "python scripts/check_messages.py %2f",
        "python scripts/check_messages.py @'PS' ",
        'python scripts/check_messages.py @"PS"',
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "forbidden" in out or "ERROR" in out

    assert calls == []


def test_run_command_blocks_multistep_decoding_bypass_vectors(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        # 2-step percent encoding of shell separators.
        "python scripts/check_messages.py %2520--help",
        "python scripts/check_messages.py %2526 echo hacked",
        "python scripts/check_messages.py %250Apython scripts/check_agent_docs.py",
        "python scripts/check_messages.py %2525TEMP%2525",
        # Mixed obfuscation around command separator tokens.
        "python scripts/check_messages.py $%28echo hacked%29",
        "python scripts/check_messages.py @%22PS%22 ",
        "python scripts/check_messages.py @%27PS%27 ",
    ]

    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "forbidden" in out or "Allowed for profile='ci'" in out

    assert calls == []


def test_run_command_blocks_seeded_fuzz_vectors(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = set()
    for seed in range(64):
        blocked.update(_seeded_fuzz_injection_candidates(seed))

    for command in sorted(blocked):
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "forbidden" in out or "Allowed for profile='ci'" in out

    assert calls == []


def test_run_command_blocks_unicode_escape_bypass_vectors(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        # Legacy percent-U escapes can hide shell metacharacters.
        "python scripts/check_messages.py %u0026 whoami",
        "python scripts/check_messages.py %5Cu0026whoami",
        # Unicode-escaped shell operators.
        "python scripts/check_messages.py \\u0026 whoami",
        "python scripts/check_messages.py %2525u0026",  # double encoded %u-style token
    ]

    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "forbidden" in out or "Allowed for profile='ci'" in out

    assert calls == []


def test_run_command_blocks_python_path_and_quote_variants(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    blocked = [
        "python3 -m pytest tests/test_template_smoke.py -q",
        "python scripts/../agent_runtime.py --help",
        "python scripts/agent_orchestrator.py;echo bad",
        "python scripts/agent_orchestrator.py --help && python scripts/agent_orchestrator.py status --json",
        "python scripts/agent_orchestrator.py\\n--help",
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR"), out
        assert "ERROR" in out

    assert calls == []


def test_run_command_forbidden_error_reports_profile_and_allowed_set():
    module = _load_agent_tools_module()
    out = module.ToolRunner(REPO_ROOT, command_profile="owner").run_command("git commit -am test")
    assert "ERROR: git subcommand not allowed in profile='owner'" in out
    assert "Allowed: " in out
    assert "Allowed for profile='owner'" in out

    out2 = module.ToolRunner(REPO_ROOT, command_profile="ci").run_command("git commit -am test")
    assert "ERROR: git subcommand not allowed in profile='ci'" in out2
    assert "Allowed for profile='ci'" in out2


def test_run_command_blocks_repo_path_escape(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    out = runner.run_command("python -m pytest ../outside/tests -q")
    assert "ERROR: python execution profile not allowed" in out
    assert "Allowed for profile='ci'" in out

    out2 = runner.run_command("python scripts/../../outside.py")
    assert "ERROR: python execution profile not allowed" in out2
    assert "Allowed for profile='ci'" in out2
    assert calls == []

    out3 = runner.run_command("python -m pytest C:/tmp/outside.py -q")
    assert "ERROR: python execution profile not allowed" in out3
    assert "Allowed for profile='ci'" in out3


def test_run_command_profile_research_unlocks_more_non_mutating_commands(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    research = module.ToolRunner(REPO_ROOT, command_profile="research")
    ci = module.ToolRunner(REPO_ROOT, command_profile="ci")

    for command in (
        "python scripts/agent_worker.py --help",
        "python scripts/auto_runner.py --help",
    ):
        assert research.run_command(command).startswith("[exit 0]"), research.run_command(command)

    for command in (
        "python scripts/agent_worker.py --help",
        "python scripts/auto_runner.py --help",
    ):
        out = ci.run_command(command)
        assert out.startswith("ERROR: python execution profile not allowed")
        assert "Allowed for profile='ci'" in out


def test_run_command_profile_split_for_git_access(tmp_path, monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    safe_file = tmp_path / "agents" / "runtime" / "notes.txt"
    safe_file.parent.mkdir(parents=True, exist_ok=True)
    safe_file.write_text("ok\n", encoding="utf-8")

    owner = module.ToolRunner(tmp_path, command_profile="owner")
    ci = module.ToolRunner(tmp_path, command_profile="ci")

    allowed = f"git add {safe_file.relative_to(tmp_path).as_posix()}"
    assert owner.run_command(allowed).startswith("[exit 0]"), owner.run_command(allowed)
    out = ci.run_command(allowed)
    assert out.startswith("ERROR: git subcommand not allowed in profile='ci'")
    assert "Allowed for profile='ci'" in out


def test_run_command_research_profile_blocks_mutating_git_and_pip(tmp_path, monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    safe_file = tmp_path / "notes.txt"
    safe_file.write_text("ok\n", encoding="utf-8")

    runner = module.ToolRunner(tmp_path, command_profile="research")
    blocked = [
        "git add notes.txt",
        "git restore notes.txt",
        "git stash push",
        "python -m pip install requests",
        "python scripts/agent_worker.py --once",
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR:"), out
        assert "Allowed for profile='research'" in out
    assert calls == []


def test_run_command_owner_profile_blocks_mutable_git_path_escape(tmp_path, monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(tmp_path, command_profile="owner")
    blocked = [
        "git add ../outside.txt",
        "git restore ../outside.txt",
        "git add C:/tmp/outside.txt",
    ]
    for command in blocked:
        out = runner.run_command(command)
        assert out.startswith("ERROR: git subcommand not allowed in profile='owner'"), out
        assert "Allowed for profile='owner'" in out
    assert calls == []


def test_run_command_pytest_unknown_flags_are_blocked(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    out = runner.run_command("python -m pytest --capture=no tests/test_template_smoke.py")
    assert out.startswith("ERROR: python execution profile not allowed"), out
    assert "Allowed for profile='ci'" in out
    assert calls == []


def test_run_command_audit_log_records_allowed_and_blocked(monkeypatch):
    module = _load_agent_tools_module()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess(calls))

    runner = module.ToolRunner(REPO_ROOT)
    assert runner.run_command("git status").startswith("[exit 0]")
    assert runner.run_command("python -c \"print(1)\"").startswith("ERROR")

    audit_tail = runner.command_audit_tail(n=2)
    assert audit_tail, "expected audit entries"
    # Newest entry is the denied command.
    assert audit_tail[-1].startswith("blocked|ci|python -c \"print(1)\"")
    # Oldest entry is the allowed command.
    assert audit_tail[0].startswith("allowed|ci|git status")


def test_run_command_audit_log_is_bounded(tmp_path, monkeypatch):
    module = _load_agent_tools_module()
    monkeypatch.setattr(module.subprocess, "run", _deny_subprocess([]))

    runner = module.ToolRunner(REPO_ROOT)
    for i in range(module.MAX_AUDIT_ENTRIES * 2):
        command = "git status" if i % 2 == 0 else "git diff"
        runner.run_command(command)
    assert len(runner.command_audit) <= module.MAX_AUDIT_ENTRIES
    assert len(runner.command_audit_tail(n=module.MAX_AUDIT_ENTRIES + 1)) == module.MAX_AUDIT_ENTRIES


def test_run_command_profile_case_insensitive_and_unknown_profile_rejected(tmp_path):
    module = _load_agent_tools_module()

    upper = module.ToolRunner(tmp_path, command_profile="OWNER")
    assert upper.command_profile == "owner"

    with pytest.raises(module.GuardrailError):
        module.ToolRunner(tmp_path, command_profile="ops")
