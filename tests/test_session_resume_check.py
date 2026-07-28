"""Smoke coverage for the shipped session_resume_check (issue #274 part 2).

Host-proven on autofolio (crash-recovery hardening, autofolio #121); upstreamed
so every consumer gets the SessionStart crash-recovery UX. Safety contract:
the check must NEVER break a session start — always exit 0 without --strict.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

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


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("session_resume_check_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_default_audit_does_not_write_runtime_state(tmp_path: Path) -> None:
    marker = tmp_path / "keep.txt"
    marker.write_text("unchanged\n", encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 0
    assert list(tmp_path.rglob("*")) == [marker]
    assert marker.read_text(encoding="utf-8") == "unchanged\n"


def test_mutating_recovery_interfaces_are_not_exposed(tmp_path: Path) -> None:
    fix = _run(tmp_path, "--fix")
    checkpoint = _run(tmp_path, "checkpoint", "--task", "TASK-1", "--step", "x")

    assert fix.returncode == 2
    assert "unrecognized arguments: --fix" in fix.stderr
    assert checkpoint.returncode == 2
    assert not (tmp_path / "agents").exists()


def test_unexpected_failure_preserves_json_and_strict_contract(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script_module()

    def fail_build(*args, **kwargs):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(module, "build_report", fail_build)

    default_code = module.main(["--root", str(tmp_path), "--json"])
    default_payload = json.loads(capsys.readouterr().out)
    strict_code = module.main(["--root", str(tmp_path), "--json", "--strict"])
    strict_payload = json.loads(capsys.readouterr().out)

    assert default_code == 0
    assert strict_code == 1
    assert default_payload["clean"] is False
    assert strict_payload["clean"] is False
    assert "synthetic failure" in default_payload["warnings"][0]
    assert "synthetic failure" in strict_payload["warnings"][0]


def test_claim_scan_rejects_path_traversal_message_id(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_script_module()
    inbox = tmp_path / "agents" / "messages" / "inbox"
    claims = tmp_path / "agents" / "runtime" / "claims"
    victim = tmp_path / "agents" / "outside" / "VICTIM.claim"
    inbox.mkdir(parents=True)
    claims.mkdir(parents=True)
    victim.parent.mkdir(parents=True)
    victim.write_text('{"expires_at": 0, "secret": "do-not-read"}\n', encoding="utf-8")
    (inbox / "MSG-malicious.md").write_text(
        "---\n"
        "id: MSG-x/../../../outside/VICTIM\n"
        "status: claimed\n"
        "---\n",
        encoding="utf-8",
    )

    def forbid_claim_read(path: Path):
        raise AssertionError(f"unsafe claim read: {path}")

    monkeypatch.setattr(module.mq, "_read_claim", forbid_claim_read)

    findings = module.scan_claimed_stale_messages(inbox, claims, now=1.0)

    assert findings == [
        {
            "file": "MSG-malicious.md",
            "message_id": "MSG-x/../../../outside/VICTIM",
            "reason": "invalid-message-id",
        }
    ]
    assert "do-not-read" in victim.read_text(encoding="utf-8")


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
    assert commands == ["python3 -m agent_runtime.hook_runtime session-start"]
    assert session_start[0]["commandWindows"] == "py -3 -m agent_runtime.hook_runtime session-start"
