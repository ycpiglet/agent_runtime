from __future__ import annotations

import json
import os
import threading
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SUMMARY_SCRIPT = (
    REPO_ROOT
    / "src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py"
)


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    expect_zero: bool = True,
    stdout_text: bool = True,
) -> subprocess.CompletedProcess:
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


def _write_jsonl_records(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records),
        encoding="utf-8",
    )


def _start_capture_server(
    *,
    path_pattern: str = "/",
    status_code: int = 200,
    response_body: bytes = b'{"ok": true}',
):
    received: list[dict[str, Any]] = []

    class _CaptureHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(length)
            if self.path != path_pattern:
                self.send_response(404)
                self.end_headers()
                return
            received.append(
                {
                    "path": self.path,
                    "body": body,
                    "content_type": self.headers.get("Content-Type", ""),
                }
            )
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, format, *args):  # noqa: A002
            return

    server = HTTPServer(("127.0.0.1", 0), _CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, received, thread


def test_warning_summary_gate_dashboard_and_slack_payloads(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": True,
                "record_count": 1,
                "recent_contexts": 1,
                "records": [],
                "reasons": [],
                "run_id": "run-ok",
            },
            {
                "policy_passed": False,
                "record_count": 2,
                "records": [
                    {
                        "run_id": "run-fail",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-fail, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 1 warnings",
                ],
            },
        ],
    )

    dashboard_payload_path = tmp_path / "dashboard.json"
    slack_payload_path = tmp_path / "slack.json"
    result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--dashboard-json",
            str(dashboard_payload_path),
            "--slack-payload",
            str(slack_payload_path),
            "--last",
            "10",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
    )
    summary = json.loads(result.stdout.strip())
    assert summary["policy_failures"] == 1
    assert summary["policy_passed_latest"] is False

    dashboard_payload = json.loads(dashboard_payload_path.read_text(encoding="utf-8"))
    assert dashboard_payload["status"] == "warning"
    assert dashboard_payload["policy_failures"] == 1
    incident_events = [event["event_name"] for event in dashboard_payload["incidents"]]
    assert "pass39_warning_summary_gate_policy" in incident_events

    slack_payload = json.loads(slack_payload_path.read_text(encoding="utf-8"))
    assert "warning-summary gate has 1 failed report" in slack_payload["text"]


def test_warning_summary_gate_dashboard_no_failure_stays_ok(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": True,
                "record_count": 1,
                "records": [],
                "reasons": [],
            }
        ],
    )

    dashboard_payload_path = tmp_path / "dashboard-ok.json"
    slack_payload_path = tmp_path / "slack-ok.json"
    result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--dashboard-json",
            str(dashboard_payload_path),
            "--slack-payload",
            str(slack_payload_path),
            "--alert-threshold",
            "2",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
    )
    summary = json.loads(result.stdout.strip())
    assert summary["policy_failures"] == 0
    assert summary["policy_passed_latest"] is True

    dashboard_payload = json.loads(dashboard_payload_path.read_text(encoding="utf-8"))
    assert dashboard_payload["status"] == "ok"
    assert dashboard_payload["incidents"] == []

    slack_payload = json.loads(slack_payload_path.read_text(encoding="utf-8"))
    assert slack_payload["text"] == "PASS-39 warning-summary gate is healthy"


def test_warning_summary_gate_monitoring_payload_schema_and_mapping(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 2,
                "recent_contexts": 1,
                "records": [
                    {
                        "run_id": "run-monitor",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-monitor, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 2 warnings",
                ],
            }
        ],
    )

    monitoring_payload_path = tmp_path / "monitoring.json"
    result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--monitoring-json",
            str(monitoring_payload_path),
            "--alert-threshold",
            "1",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
    )
    summary = json.loads(result.stdout.strip())
    assert summary["policy_failures"] == 1

    monitoring_payload = json.loads(monitoring_payload_path.read_text(encoding="utf-8"))
    assert monitoring_payload["schema_version"] == "agent-runtime.warning-summary-gate.monitoring-v1"
    assert monitoring_payload["event_type"] == "pass39_warning_summary_gate_policy"
    assert monitoring_payload["status"] == "critical"
    assert monitoring_payload["source"] == "agent-runtime-template"
    assert monitoring_payload["alerts"]["active"] is True
    assert monitoring_payload["alerts"]["alert_threshold"] == 1
    assert monitoring_payload["metrics"]["policy_failures"] == 1


def test_warning_summary_gate_sends_to_slack_and_monitoring_endpoints(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 3,
                "recent_contexts": 1,
                "records": [
                    {
                        "run_id": "run-live",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-live, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 3 warnings",
                ],
            }
        ],
    )

    slack_server, slack_received, slack_thread = _start_capture_server(path_pattern="/slack")
    monitoring_server, monitoring_received, monitoring_thread = _start_capture_server(
        path_pattern="/monitoring"
    )
    try:
        slack_url = f"http://127.0.0.1:{slack_server.server_address[1]}/slack"
        monitoring_url = (
            f"http://127.0.0.1:{monitoring_server.server_address[1]}/monitoring"
        )
        result = _run(
            [
                PYTHON,
                str(SUMMARY_SCRIPT),
                "--path",
                str(report_path),
                "--json",
                "--send-on-ok",
                "--alert-threshold",
                "1",
                "--slack-webhook-url",
                slack_url,
                "--monitoring-endpoint-url",
                monitoring_url,
            ],
            cwd=REPO_ROOT,
            env=dict(os.environ),
        )
        assert result.returncode == 0
        summary = json.loads(result.stdout.strip())
        assert summary["policy_failures"] == 1
        assert len(slack_received) == 1
        assert len(monitoring_received) == 1
        slack_payload = json.loads(slack_received[0]["body"].decode("utf-8"))
        monitoring_payload = json.loads(monitoring_received[0]["body"].decode("utf-8"))
        assert ":warning:" in slack_payload["text"]
        assert monitoring_payload["event_type"] == "pass39_warning_summary_gate_policy"
    finally:
        slack_server.shutdown()
        monitoring_server.shutdown()
        slack_server.server_close()
        monitoring_server.server_close()
        slack_thread.join(timeout=1)
        monitoring_thread.join(timeout=1)


def test_warning_summary_gate_fail_on_send_failures_returns_nonzero(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 1,
                "records": [
                    {
                        "run_id": "run-live",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-live, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 3 warnings",
                ],
            }
        ],
    )

    fail_server, fail_received, fail_thread = _start_capture_server(
        path_pattern="/bad",
        status_code=500,
        response_body=b'{"error": "downstream"}',
    )
    try:
        bad_url = f"http://127.0.0.1:{fail_server.server_address[1]}/bad"
        result = _run(
            [
                PYTHON,
                str(SUMMARY_SCRIPT),
                "--path",
                str(report_path),
                "--json",
                "--fail-on-send-failures",
                "--send-on-ok",
                "--slack-webhook-url",
                bad_url,
            ],
            cwd=REPO_ROOT,
            env=dict(os.environ),
            expect_zero=False,
        )
        assert result.returncode == 1
        assert len(fail_received) == 1
        assert "Delivery failure(s)" in (result.stderr or "")
        assert "HTTP 500" in (result.stderr or "")
    finally:
        fail_server.shutdown()
        fail_server.server_close()
        fail_thread.join(timeout=1)


def test_warning_summary_gate_send_routing_by_threshold_only_monitoring(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 2,
                "records": [
                    {
                        "run_id": "run-live",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-live, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 2 warnings",
                ],
            }
        ],
    )

    slack_server, slack_received, slack_thread = _start_capture_server(path_pattern="/slack")
    monitoring_server, monitoring_received, monitoring_thread = _start_capture_server(
        path_pattern="/monitoring"
    )
    try:
        slack_url = f"http://127.0.0.1:{slack_server.server_address[1]}/slack"
        monitoring_url = (
            f"http://127.0.0.1:{monitoring_server.server_address[1]}/monitoring"
        )
        result = _run(
            [
                PYTHON,
                str(SUMMARY_SCRIPT),
                "--path",
                str(report_path),
                "--json",
                "--alert-threshold",
                "1",
                "--monitoring-threshold",
                "1",
                "--slack-threshold",
                "3",
                "--slack-webhook-url",
                slack_url,
                "--monitoring-endpoint-url",
                monitoring_url,
            ],
            cwd=REPO_ROOT,
            env=dict(os.environ),
        )
        assert result.returncode == 0
        assert len(slack_received) == 0
        assert len(monitoring_received) == 1
        monitoring_payload = json.loads(
            monitoring_received[0]["body"].decode("utf-8")
        )
        assert monitoring_payload["event_type"] == "pass39_warning_summary_gate_policy"
    finally:
        slack_server.shutdown()
        monitoring_server.shutdown()
        slack_server.server_close()
        monitoring_server.server_close()
        slack_thread.join(timeout=1)
        monitoring_thread.join(timeout=1)


def test_warning_summary_gate_invalid_targets_are_safe_skipped(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 1,
                "records": [
                    {
                        "run_id": "run-live",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-live, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 1 warnings",
                ],
            }
        ],
    )

    result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--alert-threshold",
            "1",
            "--slack-webhook-url",
            "YOUR_SLACK_WEBHOOK_URL",
            "--monitoring-endpoint-url",
            "https://example.com/bad-target",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
    )
    assert result.returncode == 0
    assert "Delivery skipped: Slack target not used" in (result.stderr or "")


def test_warning_summary_gate_invalid_targets_fail_when_required(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": False,
                "record_count": 1,
                "records": [
                    {
                        "run_id": "run-live",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [
                    "context(run_id=run-live, event=smoke) code=PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE has 1 warnings",
                ],
            }
        ],
    )

    result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--alert-threshold",
            "1",
            "--slack-webhook-url",
            "YOUR_SLACK_WEBHOOK_URL",
            "--monitoring-endpoint-url",
            "https://example.com/bad-target",
            "--require-send-targets",
            "--fail-on-send-failures",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
        expect_zero=False,
    )
    assert result.returncode == 1
    assert "missing valid send targets" in (result.stderr or "")


def test_warning_summary_gate_require_send_targets_only_enforced_when_send_is_needed(tmp_path):
    report_path = tmp_path / "template-warning-summary-gate-report.jsonl"
    _write_jsonl_records(
        report_path,
        [
            {
                "policy_passed": True,
                "record_count": 1,
                "records": [
                    {
                        "run_id": "run-ok",
                        "event_name": "smoke",
                        "window_start": "2026-06-09T00:00:00Z",
                        "window_end": "2026-06-09T00:01:00Z",
                    }
                ],
                "reasons": [],
            }
        ],
    )

    non_send_result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--alert-threshold",
            "5",
            "--require-send-targets",
            "--slack-webhook-url",
            "YOUR_SLACK_WEBHOOK_URL",
            "--monitoring-endpoint-url",
            "https://example.com/invalid-monitor",
            "--fail-on-send-failures",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
    )
    assert non_send_result.returncode == 0
    assert "Delivery skipped" not in (non_send_result.stderr or "")

    send_result = _run(
        [
            PYTHON,
            str(SUMMARY_SCRIPT),
            "--path",
            str(report_path),
            "--json",
            "--alert-threshold",
            "1",
            "--require-send-targets",
            "--fail-on-send-failures",
            "--send-on-ok",
            "--slack-webhook-url",
            "YOUR_SLACK_WEBHOOK_URL",
            "--monitoring-endpoint-url",
            "https://example.com/invalid-monitor",
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
        expect_zero=False,
    )
    assert send_result.returncode == 1
    assert "missing valid send targets" in (send_result.stderr or "")
