from __future__ import annotations

import os
import shutil
import subprocess
import sys
import json
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None,
         expect_zero: bool = True, stdout_text: bool = True) -> subprocess.CompletedProcess:
    if env is None:
        env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=stdout_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if expect_zero and result.returncode != 0:
        detail = result.stdout or result.stderr or "<no output>"
        raise AssertionError(
            f"command failed ({command!r}) returncode={result.returncode}. output:\n{detail}"
        )
    return result


def _host_from_fixture(tmp_path: Path) -> Path:
    host = tmp_path / "host"
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "host", host)
    return host


def _parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    out: dict[str, str] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line:
            continue
        if ": " not in line and ":" not in line:
            continue
        key, sep, value = line.partition(":")
        out[key.strip()] = (value[1:] if sep else "").strip()
    return out


def _write_message(inbox: Path, message_id: str, *, status: str = "open") -> Path:
    path = inbox / f"{message_id}.md"
    path.write_text(
        "\n".join(
            [
                "---",
                f"id: {message_id}",
                "from: orchestrator",
                "to: qa",
                "type: question",
                f"status: {status}",
                "task_id: none",
                "intent: template smoke",
                "ts: 2026-06-08T11:11:11+09:00",
                "---",
                "run one dummy response",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_sync_and_smoke_runtime_scripts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync_result = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync_result.returncode == 0
    assert "applied=" in (sync_result.stdout or "")

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    (host / "agents" / "messages").mkdir(parents=True, exist_ok=True)
    (host / "agents" / "runtime" / "events").mkdir(parents=True, exist_ok=True)
    scripts_dir = host / "scripts"
    for script in ("agent_orchestrator.py", "agent_worker.py", "auto_runner.py", "check_messages.py"):
        result = _run(
            [PYTHON, str(scripts_dir / script), "--help"] if script != "check_messages.py" else [PYTHON, str(scripts_dir / script)],
            cwd=host,
            env=command_env,
        )
        assert result.returncode == 0


def test_worker_processes_one_dummy_message(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    report_path = Path(
        os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH",
            str(tmp_path / "template-warning-summary-gate-report.jsonl"),
        )
    )

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    message_id = "MSG-20260608-111111-aaaaaa"
    incoming = _write_message(inbox, message_id)

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    worker = _run(
        [PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy", "--once", "--quiet"],
        cwd=host,
        env=command_env,
    )
    assert worker.returncode == 0

    source = _parse_frontmatter(incoming)
    assert source.get("status") == "answered"
    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name != incoming.name]
    assert replies, "worker should create a reply message file"
    parsed = [_parse_frontmatter(p) for p in replies]
    assert any(p.get("type") == "reply" and p.get("in_reply_to") == message_id for p in parsed)


def test_sync_does_not_seed_default_claim_artifacts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync_result = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync_result.returncode == 0

    claim_dir = host / "agents" / "runtime" / "claims"
    assert not claim_dir.exists() or not any(p.suffix == ".claim" for p in claim_dir.glob("*.claim"))


def test_concurrent_workers_on_same_message_generate_single_reply(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    message_id = "MSG-20260608-999999-race"
    incoming = _write_message(inbox, message_id)

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")

    command = [
        PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy",
        "--once", "--timeout", "4", "--poll-interval", "0.1", "--quiet",
    ]
    p1 = subprocess.Popen(
        command,
        cwd=host,
        env=command_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # Small overlap window to stress the claim race.
    time.sleep(0.05)
    p2 = subprocess.Popen(
        command,
        cwd=host,
        env=command_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    out1, err1 = p1.communicate(timeout=20)
    out2, err2 = p2.communicate(timeout=20)
    assert p1.returncode == 0, out1 + err1
    assert p2.returncode == 0, out2 + err2

    source = _parse_frontmatter(incoming)
    assert source.get("status") == "answered"

    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name != incoming.name]
    assert len(replies) == 1, replies
    parsed = [_parse_frontmatter(p) for p in replies]
    assert parsed[0].get("type") == "reply"
    assert parsed[0].get("in_reply_to") == message_id


def test_worker_processes_multiple_messages_with_stale_recovery(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    inbox = host / "agents" / "messages" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    runtime = host / "agents" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    claim_dir = runtime / "claims"
    claim_dir.mkdir(parents=True, exist_ok=True)

    message_ids = [
        "MSG-20260608-111111-batch",
        "MSG-20260608-222222-batch",
        "MSG-20260608-333333-batch",
    ]
    messages = [_write_message(inbox, message_id) for message_id in message_ids]

    stale_claim = {
        "message_id": message_ids[1],
        "role": "qa",
        "pid": 12345,
        "hostname": "stale-worker",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": message_ids[1],
    }
    (claim_dir / f"{message_ids[1]}.claim").write_text(
        json.dumps(stale_claim, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    worker = _run(
        [
            PYTHON, "scripts/agent_worker.py", "--role", "qa", "--provider", "dummy",
            "--poll-interval", "0.05", "--timeout", "6", "--quiet"
        ],
        cwd=host,
        env=command_env,
    )
    assert worker.returncode == 0

    claimed = [_parse_frontmatter(p).get("status") for p in messages]
    assert all(s == "answered" for s in claimed), claimed

    replies = [p for p in inbox.iterdir() if p.suffix == ".md" and p.name not in {m.name for m in messages}]
    assert len(replies) == len(message_ids), replies
    reply_targets = {
        _parse_frontmatter(r).get("in_reply_to")
        for r in replies
    }
    assert reply_targets == set(message_ids)

    assert not (claim_dir / f"{message_ids[1]}.claim").exists()


def test_warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts(tmp_path):
    host = _host_from_fixture(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    report_path = Path(
        os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH",
            str(tmp_path / "template-warning-summary-gate-report.jsonl"),
        )
    )

    sync = _run(
        [PYTHON, "-m", "agent_runtime.cli", "sync", "--root", str(host), "--apply"],
        cwd=REPO_ROOT,
        env=env,
    )
    assert sync.returncode == 0

    summary_path = tmp_path / "template-warning-summaries.jsonl"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_records = [
        {
            "schema_version": "pass39-warning-summary-v0",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            },
            "run": "run-template-smoke-76",
            "event": "smoke",
            "ts_window_start": "2026-06-09T00:00:00Z",
            "window_end_time": "2026-06-09T00:01:00Z",
            "total_warnings": 2,
        },
        {
            "schema_version": "pass39-warning-summary-legacy",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            },
            "run": "run-template-smoke-76",
            "event": "smoke",
            "window": "2026-06-09T00:00:00Z/2026-06-09T00:01:00Z",
            "total_warnings": 1,
        },
    ]
    summary_path.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in legacy_records) + "\n",
        encoding="utf-8",
    )

    command_env = dict(os.environ)
    command_env["PYTHONPATH"] = str(host / "scripts")
    command = [
        PYTHON,
        "scripts/message_queue.py",
        "warning-summary-gate",
        "--summary-path",
        str(summary_path),
        "--run-id",
        "run-template-smoke-76",
        "--event-name",
        "smoke",
        "--window-start",
        "2026-06-09T00:00:00Z",
        "--window-end",
        "2026-06-09T00:01:00Z",
        "--warning",
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=1",
        "--max-warnings-per-context",
        "2",
        "--code-threshold",
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=2",
        "--report-path",
        str(report_path),
    ]
    pass_result = _run(command, cwd=host, env=command_env)
    pass_report = json.loads(pass_result.stdout.strip())
    assert pass_report["policy_passed"] is True
    assert pass_report["record_count"] == 1
    merged = pass_report["records"][0]
    assert merged["schema_version"] == "pass39-warning-summary-legacy"
    assert merged["total_warnings"] == 2
    assert merged["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 1
    assert report_path.exists()
    artifact_records = [
        json.loads(line)
        for line in report_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(artifact_records) == 1
    assert artifact_records[0]["record_count"] == 1
    assert artifact_records[0]["code_warning_limits"].get("PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE") == 2

    fail_command = list(command)
    fail_command[fail_command.index("--max-warnings-per-context") + 1] = "1"
    fail_result = _run(fail_command, cwd=host, env=command_env, expect_zero=False)
    fail_report = json.loads(fail_result.stdout.strip())
    assert fail_result.returncode != 0
    assert fail_report["policy_passed"] is False
    assert any("max 1" in reason for reason in fail_report["reasons"])

    code_fail_command = list(command)
    code_fail_command[code_fail_command.index("--max-warnings-per-context") + 1] = "99"
    threshold_arg_index = code_fail_command.index("--code-threshold") + 1
    code_fail_command[threshold_arg_index] = (
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE=0"
    )
    code_fail_result = _run(
        code_fail_command,
        cwd=host,
        env=command_env,
        expect_zero=False,
    )
    code_fail_report = json.loads(code_fail_result.stdout.strip())
    assert code_fail_result.returncode != 0
    assert code_fail_report["policy_passed"] is False
    assert any(
        "code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE" in reason
        for reason in code_fail_report["reasons"]
    )

    dry_run_command = list(code_fail_command)
    dry_run_command.extend(["--dry-run"])
    dry_run_result = _run(dry_run_command, cwd=host, env=command_env)
    dry_run_report = json.loads(dry_run_result.stdout.strip())
    assert dry_run_result.returncode == 0
    assert dry_run_report["policy_passed"] is False
    assert dry_run_report["dry_run"] is True
