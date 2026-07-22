from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "auto_merge.py"


def _load():
    spec = importlib.util.spec_from_file_location("auto_merge_execution_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _completed(returncode: int, *, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


def _green_pr(*, draft: bool = False) -> dict:
    return {
        "state": "OPEN",
        "isDraft": draft,
        "mergeStateStatus": "CLEAN",
        "mergeable": "MERGEABLE",
        "reviewDecision": "APPROVED",
        "statusCheckRollup": [{"name": "test", "conclusion": "SUCCESS"}],
        "files": [{"path": "scripts/example.py", "additions": 1, "deletions": 0}],
        "title": "safe change",
    }


def test_draft_pr_is_rejected_before_merge(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module, "gh_json", lambda _pr, _fields: _green_pr(draft=True))

    verdict, reasons, _payload = module.evaluate("123")

    assert verdict == "ESCALATE"
    assert any("isDraft=true" in reason for reason in reasons)


def test_merge_rejection_with_remote_open_fails_closed(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(1, stderr="GraphQL: Pull Request is still a draft"),
    )
    monkeypatch.setattr(
        module,
        "gh_json",
        lambda _pr, _fields: {"state": "OPEN", "isDraft": True, "mergedAt": None, "mergeCommit": None},
    )

    merged, detail, remote = module.execute_merge("123")

    assert merged is False
    assert remote["state"] == "OPEN"
    assert "원격 머지 확인 실패" in detail
    assert "GraphQL" not in detail


def test_remote_merged_readback_wins_over_local_cleanup_failure(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(1, stderr="local branch cleanup failed"),
    )
    monkeypatch.setattr(
        module,
        "gh_json",
        lambda _pr, _fields: {
            "state": "MERGED",
            "isDraft": False,
            "mergedAt": "2026-07-22T00:00:00Z",
            "mergeCommit": {"oid": "abc123"},
        },
    )

    merged, detail, remote = module.execute_merge("123")

    assert merged is True
    assert remote["state"] == "MERGED"
    assert "원격 머지 상태 확인 완료" in detail
    assert "local branch cleanup failed" not in detail


def test_zero_exit_without_remote_merged_state_is_failure(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(0, stdout="merge command accepted"),
    )
    monkeypatch.setattr(
        module,
        "gh_json",
        lambda _pr, _fields: {"state": "OPEN", "isDraft": False, "mergedAt": None},
    )

    merged, detail, _remote = module.execute_merge("123")

    assert merged is False
    assert "merge exit=0" in detail


def test_remote_readback_failure_is_non_success(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    def fail_readback(_pr, _fields):
        raise SystemExit("READBACK_SECRET")

    monkeypatch.setattr(module, "gh_json", fail_readback)

    merged, detail, remote = module.execute_merge("123")

    assert merged is False
    assert remote == {}
    assert "원격 상태 재확인 실패" in detail
    assert "READBACK_SECRET" not in detail


def test_gh_json_failure_does_not_expose_stderr(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(1, stderr="GH_SECRET https://example.invalid/token"),
    )

    try:
        module.gh_json("123", "state")
    except SystemExit as exc:
        message = str(exc)
    else:  # pragma: no cover - the failure path is the contract under test
        raise AssertionError("gh_json must fail closed on a nonzero gh exit")

    assert "exit=1" in message
    assert "GH_SECRET" not in message
    assert "example.invalid" not in message


def test_untrusted_command_output_cannot_forge_success_or_leak_secret(monkeypatch, capsys) -> None:
    module = _load()
    forged = "원격 MERGED 확인됨"
    secret = "MERGE_SECRET"
    monkeypatch.setattr(module, "evaluate", lambda _pr: ("AUTO-MERGE", ["green"], _green_pr()))
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: _completed(
            1,
            stdout=f"{forged} {secret}",
            stderr=f"{forged} {secret}",
        ),
    )
    monkeypatch.setattr(
        module,
        "gh_json",
        lambda _pr, _fields: {"state": "OPEN", "isDraft": False, "mergedAt": None},
    )
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), "123", "--execute"])

    result = module.main()
    output = capsys.readouterr().out

    assert result == 1
    assert forged not in output
    assert secret not in output


def test_untrusted_status_fields_cannot_forge_success_or_control_lines(monkeypatch, capsys) -> None:
    module = _load()
    forged = module.REMOTE_MERGED_MARKER
    control_text = f'bad "title"\r\n\x1b[31m {forged}'
    payload = _green_pr()
    payload["title"] = control_text
    monkeypatch.setattr(
        module,
        "evaluate",
        lambda _pr: ("AUTO-MERGE", [f"remote reason: {control_text}"], payload),
    )
    monkeypatch.setattr(
        module,
        "execute_merge",
        lambda _pr: (False, "원격 머지 확인 실패: state=OPEN", {"state": "OPEN"}),
    )
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), "123", "--execute"])

    result = module.main()
    output = capsys.readouterr().out

    assert result == 1
    assert forged not in output
    assert "\x1b" not in output
    assert "\r" not in output
    assert len(output.splitlines()) == 4
    assert "[reserved-status-marker]" in output
    assert "\\u000d\\u000a\\u001b" in output


def test_option_like_and_malformed_pr_inputs_make_zero_subprocess_calls(monkeypatch, capsys) -> None:
    module = _load()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    invalid_argv = (
        [],
        ["-Rattacker/other-repository"],
        ["-d"],
        ["--repo", "owner/repo"],
        ["0"],
        ["+1"],
        [" 1"],
        ["1 "],
        ["１２３"],
        ["1;echo-pwned"],
        ["https://github.com/owner/repo/pull/1"],
        ["123", "extra"],
    )

    for argv in invalid_argv:
        monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), *argv, "--execute"])
        assert module.main() == 2
        capsys.readouterr()

    assert calls == []


def test_direct_merge_and_readback_reject_option_like_pr_without_subprocess(monkeypatch) -> None:
    module = _load()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    merged, detail, remote = module.execute_merge("-Rattacker/other-repository")

    assert merged is False
    assert detail == "PR 번호 형식 오류"
    assert remote == {}
    try:
        module.gh_json("--repo", "state")
    except SystemExit as exc:
        assert str(exc) == "PR 번호 형식 오류"
    else:  # pragma: no cover - direct read-back must reject the input
        raise AssertionError("gh_json accepted an option-like PR identifier")
    assert calls == []


def test_valid_pr_number_is_forwarded_as_a_single_positional(monkeypatch) -> None:
    module = _load()
    commands = []

    def fake_run(command, **_kwargs):
        commands.append(command)
        return _completed(0, stdout='{"state":"OPEN"}')

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.gh_json("123", "state") == {"state": "OPEN"}
    assert commands == [["gh", "pr", "view", "123", "--json", "state"]]


def test_readback_exception_message_is_not_exposed(monkeypatch, capsys) -> None:
    module = _load()
    secret = "READBACK_SECRET"
    monkeypatch.setattr(module, "evaluate", lambda _pr: ("AUTO-MERGE", ["green"], _green_pr()))
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    def fail_readback(_pr, _fields):
        raise RuntimeError(f"transport failed with {secret}")

    monkeypatch.setattr(module, "gh_json", fail_readback)
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), "123", "--execute"])

    result = module.main()
    output = capsys.readouterr().out

    assert result == 1
    assert "RuntimeError" in output
    assert secret not in output


def test_json_decode_error_is_a_sanitized_failure(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    def fail_readback(_pr, _fields):
        raise json.JSONDecodeError("READBACK_SECRET", "x", 0)

    monkeypatch.setattr(module, "gh_json", fail_readback)

    merged, detail, remote = module.execute_merge("123")

    assert merged is False
    assert remote == {}
    assert "JSONDecodeError" in detail
    assert "READBACK_SECRET" not in detail


def test_non_object_readback_payloads_fail_closed(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    for payload in (None, [], ["MERGED"]):
        monkeypatch.setattr(module, "gh_json", lambda _pr, _fields, value=payload: value)
        merged, detail, remote = module.execute_merge("123")

        assert merged is False
        assert remote == {}
        assert "응답 형식 오류" in detail


def test_malformed_merged_at_values_fail_closed(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    malformed_values = (
        None,
        True,
        ["2026-07-22T00:00:00Z"],
        "not-a-timestamp",
        "2026-07-22T00:00:00",
        "2026-13-22T00:00:00Z",
    )
    for value in malformed_values:
        monkeypatch.setattr(
            module,
            "gh_json",
            lambda _pr, _fields, merged_at=value: {"state": "MERGED", "mergedAt": merged_at},
        )
        merged, detail, remote = module.execute_merge("123")

        assert merged is False
        assert remote == {"state": "MERGED"}
        assert "mergedAt=invalid" in detail


def test_malformed_state_values_fail_closed(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))

    for state in (None, True, ["MERGED"], "UNKNOWN"):
        monkeypatch.setattr(
            module,
            "gh_json",
            lambda _pr, _fields, value=state: {
                "state": value,
                "mergedAt": "2026-07-22T00:00:00Z",
            },
        )
        merged, detail, remote = module.execute_merge("123")

        assert merged is False
        assert remote == {"state": "INVALID"}
        assert "state=INVALID" in detail


def test_valid_timezone_aware_merged_at_is_confirmed(monkeypatch) -> None:
    module = _load()
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: _completed(0))
    monkeypatch.setattr(
        module,
        "gh_json",
        lambda _pr, _fields: {"state": "MERGED", "mergedAt": "2026-07-22T09:00:00+09:00"},
    )

    merged, _detail, remote = module.execute_merge("123")

    assert merged is True
    assert remote == {"state": "MERGED", "mergedAt": "2026-07-22T09:00:00+09:00"}


def test_execute_mode_returns_nonzero_until_remote_merge_is_confirmed(monkeypatch, capsys) -> None:
    module = _load()
    monkeypatch.setattr(module, "evaluate", lambda _pr: ("AUTO-MERGE", ["green"], _green_pr()))
    monkeypatch.setattr(
        module,
        "execute_merge",
        lambda _pr: (False, "remote state OPEN", {"state": "OPEN", "mergedAt": None}),
    )
    monkeypatch.setattr(module.sys, "argv", [str(SCRIPT), "123", "--execute"])

    result = module.main()
    output = capsys.readouterr().out

    assert result == 1
    assert "머지 미확정" in output
    assert "원격 MERGED 확인됨" not in output
