from __future__ import annotations

import importlib.util
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
    assert "원격 상태가 MERGED가 아님" in detail
    assert "GraphQL" in detail


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
    assert "원격 MERGED 상태로 성공 확정" in detail


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
        raise SystemExit("gh failed")

    monkeypatch.setattr(module, "gh_json", fail_readback)

    merged, detail, remote = module.execute_merge("123")

    assert merged is False
    assert remote == {}
    assert "원격 상태 재확인 실패" in detail


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
