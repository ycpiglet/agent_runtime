from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import doctor
from agent_runtime import state_projection

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_TEMPLATES = PACKAGE_ROOT / "src" / "agent_runtime" / "templates" / "project"


def _write_host_config(root: Path) -> None:
    (root / "agent_runtime.yml").write_text(
        "\n".join(
            [
                "project: fixture-host",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.6",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _copy_project_templates(root: Path) -> None:
    for child in SOURCE_TEMPLATES.iterdir():
        target = root / child.name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _prepare_host_root(tmp_path: Path, *, with_lock: bool = False) -> Path:
    host = tmp_path / "host"
    _copy_project_templates(host)
    _write_host_config(host)
    (host / "agents" / "messages" / "inbox").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "messages" / "archive").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "messages" / "samples").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "runtime" / "claims").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "runtime" / "events").mkdir(parents=True, exist_ok=True)
    if with_lock:
        result = cli_module.main(["lock", "--root", str(host), "--write"])
        assert result == 0
    return host


def _write_message_file(root: Path, message_id: str, *, status: str = "claimed", in_reply_to: str | None = None) -> Path:
    inbox = root / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    body = "question body\n"
    msg = [
        "---",
        f"id: {message_id}",
        "from: orchestrator",
        "to: qa",
        "type: question",
        f"status: {status}",
        "ts: 2026-06-08T11:11:11+09:00",
        f"intent: test",
        "task_id: none",
        f"in_reply_to: {in_reply_to}" if in_reply_to else "",
        "---",
        body,
        "",
    ]
    path = inbox / f"{message_id}.md"
    path.write_text("\n".join([line for line in msg if line != ""]), encoding="utf-8")
    return path


def test_doctor_check_fails_on_missing_core_template_file(tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)
    (root / "scripts" / "orchestrator_safety_gate.py").unlink()

    rc = cli_module.main(["doctor", "--root", str(root), "--check"])
    assert rc == 1

    plan, _ = doctor.build_doctor_plan(root)
    assert any(
        f.path == "scripts/orchestrator_safety_gate.py" and f.kind == "missing-required-file"
        and f.severity == "blocker"
        for f in plan.findings
    )


def test_doctor_detects_stale_claim_without_reply(tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)
    inbox = root / "agents" / "messages" / "inbox"
    _write_message_file(root, "MSG-20260608-111111-stale")
    claim_path = root / "agents" / "runtime" / "claims" / "MSG-20260608-111111-stale.claim"
    claim_path.write_text(
        '{"message_id":"MSG-20260608-111111-stale","role":"qa","pid":1,"hostname":"host",'
        '"claimed_at":1,"expires_at":0,"path":"MSG-20260608-111111-stale"}',
        encoding="utf-8",
    )

    plan, _ = doctor.build_doctor_plan(root)
    assert any(
        f.path == "agents/runtime/claims/MSG-20260608-111111-stale.claim"
        and f.kind == "stale-claim-without-reply"
        and f.severity == "warning"
        for f in plan.findings
    )


def test_doctor_reports_provider_import_failure_as_warning(monkeypatch, tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)

    def fake_import(root_path: Path, module_name: str) -> tuple[bool, str | None]:
        if module_name == "providers.codex":
            return False, "missing dependency or module: requests"
        return True, None

    monkeypatch.setattr(doctor, "_module_import_check", fake_import)

    plan, _ = doctor.build_doctor_plan(root)
    assert any(
        f.area == "provider-imports"
        and f.path == "providers/codex.py"
        and f.severity == "warning"
        for f in plan.findings
    )


def test_doctor_success_for_synced_host(tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)

    rc = cli_module.main(["doctor", "--root", str(root), "--check"])
    assert rc == 0
    output = doctor.render(doctor.build_doctor_plan(root)[0])
    assert "blockers=0" in output
    plan, _ = doctor.build_doctor_plan(root)
    assert not any(
        f.kind == "toolrunner-audit-missing" for f in plan.findings
    )


def test_doctor_reports_scribe_missing_overdue_and_fresh_without_writing(tmp_path):
    root = _prepare_host_root(tmp_path)
    (root / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: fixture-host\n"
        "sync:\n"
        "  mode: check-diff-apply\n"
        "  allow_silent_overwrite: false\n"
        "host:\n"
        "  state_adapters:\n"
        "    status: STATUS.md\n",
        encoding="utf-8",
    )
    source = root / "STATUS.md"
    source.write_text(
        "# State\n" + "".join(f"- active {index}\n" for index in range(16)),
        encoding="utf-8",
    )
    source_mtime = source.stat().st_mtime_ns

    missing, _ = doctor.build_doctor_plan(root)
    kinds = {finding.kind for finding in missing.findings if finding.area == "scribe"}
    assert {"scribe-overdue", "projection-missing"}.issubset(kinds)
    assert missing.scribe and missing.scribe["closure_blocking"] is True
    assert not (root / state_projection.DEFAULT_PROJECTION_PATH).exists()
    assert source.stat().st_mtime_ns == source_mtime

    state_projection.write_projection(
        root, now="2026-07-29T00:00:00+09:00"
    )
    projection = root / state_projection.DEFAULT_PROJECTION_PATH
    projection_mtime = projection.stat().st_mtime_ns
    fresh, _ = doctor.build_doctor_plan(root)
    assert any(
        finding.area == "scribe" and finding.kind == "projection-fresh"
        for finding in fresh.findings
    )
    assert fresh.scribe and fresh.scribe["closure_blocking"] is False
    assert source.stat().st_mtime_ns == source_mtime
    assert projection.stat().st_mtime_ns == projection_mtime


def test_doctor_blocks_invalid_config(tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)
    (root / "agent_runtime.yml").unlink()

    rc = cli_module.main(["doctor", "--root", str(root), "--check"])
    assert rc == 1

    plan, _ = doctor.build_doctor_plan(root)
    assert any(f.area == "config" and f.kind == "config-invalid" and f.severity == "blocker" for f in plan.findings)


def test_doctor_repair_creates_missing_runtime_dirs(tmp_path):
    root = _prepare_host_root(tmp_path, with_lock=True)
    shutil.rmtree(root / "agents" / "runtime" / "events")
    shutil.rmtree(root / "agents" / "runtime" / "claims")
    shutil.rmtree(root / "agents" / "messages" / "inbox")
    (root / "agents" / "messages").mkdir(parents=True, exist_ok=True)

    rc = cli_module.main(["doctor", "--root", str(root), "--repair"])
    assert rc == 0
    assert (root / "agents" / "runtime" / "events").exists()
    assert (root / "agents" / "runtime" / "claims").exists()
    assert (root / "agents" / "messages" / "inbox").exists()


def test_doctor_repair_removes_stale_claim(tmp_path, capsys):
    root = _prepare_host_root(tmp_path, with_lock=True)
    claim_path = root / "agents" / "runtime" / "claims" / "MSG-20260608-111111-stale.claim"
    claim_path.write_text(
        json.dumps(
            {
                "message_id": "MSG-20260608-111111-stale",
                "role": "qa",
                "pid": 1,
                "hostname": "host",
                "claimed_at": 1,
                "expires_at": 0,
                "path": "MSG-20260608-111111-stale",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_message_file(root, "MSG-20260608-111111-stale")

    rc = cli_module.main(["doctor", "--root", str(root), "--repair"])
    captured = capsys.readouterr()
    assert rc == 0
    assert not claim_path.exists()
    assert "removed_stale_claim" in captured.out


def test_doctor_repair_reports_no_action_when_clean(tmp_path, capsys):
    root = _prepare_host_root(tmp_path, with_lock=True)
    for old_claim in (root / "agents" / "runtime" / "claims").glob("*.claim"):
        old_claim.unlink()
    rc = cli_module.main(["doctor", "--root", str(root), "--repair"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "no actions needed" in captured.out


def test_doctor_repair_json_does_not_mix_human_output(tmp_path, capsys):
    root = _prepare_host_root(tmp_path, with_lock=True)
    capsys.readouterr()
    assert cli_module.main(["doctor", "--root", str(root), "--repair", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "agent-runtime-doctor/v1"
    assert "repair_actions" in payload


def _codex_hook_findings(root: Path) -> list[doctor.DoctorFinding]:
    findings: list[doctor.DoctorFinding] = []
    doctor._check_codex_hooks(root, findings)
    return findings


def _hook_payload(root: Path) -> dict:
    path = root / ".codex" / "hooks.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _write_hook_payload(root: Path, payload: dict) -> None:
    (root / ".codex" / "hooks.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_codex_hook_contract_accepts_valid_hooks_and_requires_trust_review(tmp_path):
    root = _prepare_host_root(tmp_path)

    findings = _codex_hook_findings(root)

    assert not any(item.severity == "blocker" for item in findings)
    assert [item.kind for item in findings] == ["trust-review"]


def test_codex_hook_contract_reports_malformed_file_without_trust_claim(tmp_path):
    root = _prepare_host_root(tmp_path)
    (root / ".codex" / "hooks.json").write_text("{", encoding="utf-8")

    findings = _codex_hook_findings(root)

    assert any(item.kind == "malformed-hooks" for item in findings)
    assert not any(item.kind == "trust-review" for item in findings)


def test_codex_hook_contract_reports_missing_mode_but_allows_foreign_hook(tmp_path):
    root = _prepare_host_root(tmp_path)
    payload = _hook_payload(root)
    payload["hooks"].pop("PostCompact")
    payload["hooks"]["SessionStart"].append(
        {"hooks": [{"type": "command", "command": "foreign command"}]}
    )
    _write_hook_payload(root, payload)

    findings = _codex_hook_findings(root)

    assert any(
        item.kind == "missing-required-mode" and "post-compact" in item.detail
        for item in findings
    )
    assert not any(
        item.kind == "stale-hook-command" and "foreign" in item.detail
        for item in findings
    )
    assert not any(item.kind == "trust-review" for item in findings)


def test_codex_hook_contract_reports_missing_windows_command(tmp_path):
    root = _prepare_host_root(tmp_path)
    payload = _hook_payload(root)
    payload["hooks"]["SessionStart"][0]["hooks"][0].pop("commandWindows")
    _write_hook_payload(root, payload)

    findings = _codex_hook_findings(root)

    assert any(item.kind == "missing-command-windows" for item in findings)


def test_codex_hook_contract_reports_stale_posix_and_windows_commands(tmp_path):
    root = _prepare_host_root(tmp_path)
    payload = _hook_payload(root)
    hook = payload["hooks"]["SessionStart"][0]["hooks"][0]
    hook["command"] = r"scripts\session_start_hook.cmd"
    hook["commandWindows"] = r"C:\Python310\python.exe scripts\session_start_hook.py"
    _write_hook_payload(root, payload)

    findings = _codex_hook_findings(root)
    kinds = {item.kind for item in findings}

    assert "stale-hook-command" in kinds
    assert "stale-command-windows" in kinds
    assert "missing-required-mode" in kinds


def test_codex_hook_contract_reports_missing_dispatch_target(tmp_path):
    root = _prepare_host_root(tmp_path)
    (root / "scripts" / "session_compact_hook.py").unlink()

    findings = _codex_hook_findings(root)

    assert any(
        item.kind == "missing-hook-target"
        and item.path == "scripts/session_compact_hook.py"
        for item in findings
    )
