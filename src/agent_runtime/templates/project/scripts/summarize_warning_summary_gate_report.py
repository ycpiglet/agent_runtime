#!/usr/bin/env python3
"""Summarize PASS-39 warning-summary gate report artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_codes_from_reason(reason: str) -> list[str]:
    return re.findall(r"code=([A-Z0-9_]+)", reason)


def _load_report_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def _summarize(records: list[dict], *, last: int | None) -> tuple[int, dict]:
    if last is not None and last > 0:
        records = records[-last:]
    if not records:
        return 0, {
            "total_reports": 0,
            "policy_failures": 0,
            "policy_passed_latest": None,
            "failed_reasons_top": [],
            "failed_codes_top": [],
            "latest_summary_records": 0,
            "recent_contexts": 0,
        }

    policy_failures = sum(1 for item in records if item.get("policy_passed") is False)
    failed_reasons: list[str] = []
    failed_codes: Counter[str] = Counter()
    contexts: set[tuple[str, str, str, str]] = set()
    for item in records:
        reasons = item.get("reasons") or []
        if item.get("policy_passed") is False:
            failed_reasons.extend(str(reason) for reason in reasons)
            for reason in reasons:
                for code in _extract_codes_from_reason(str(reason)):
                    failed_codes[code] += 1
        for record in item.get("records", []) if isinstance(item.get("records"), list) else []:
            contexts.add(
                (
                    str(record.get("run_id", "unknown")),
                    str(record.get("event_name", "unknown")),
                    str(record.get("window_start", "")),
                    str(record.get("window_end", "")),
                )
            )
    reason_counter = Counter(failed_reasons)
    summary = {
        "total_reports": len(records),
        "policy_failures": policy_failures,
        "policy_passed_latest": bool(records[-1].get("policy_passed")),
        "failed_reasons_top": [
            {"reason": reason, "count": count}
            for reason, count in reason_counter.most_common(5)
        ],
        "failed_codes_top": [
            {"code": code, "count": count}
            for code, count in failed_codes.most_common(5)
        ],
        "latest_summary_records": _safe_int(records[-1].get("record_count", 0)),
        "recent_contexts": len(contexts),
    }
    return policy_failures, summary


def _render_text(summary: dict) -> str:
    lines = [
        "Warning summary gate report snapshot:",
        f"- total_reports: {summary['total_reports']}",
        f"- policy_failures: {summary['policy_failures']}",
        f"- policy_passed_latest: {summary['policy_passed_latest']}",
        f"- latest_summary_records: {summary['latest_summary_records']}",
        f"- recent_contexts: {summary['recent_contexts']}",
    ]
    if summary["policy_failures"]:
        lines.append("- failed_reasons_top:")
        for item in summary["failed_reasons_top"]:
            lines.append(f"  - {item['reason']} ({item['count']})")
        lines.append("- failed_codes_top:")
        for item in summary["failed_codes_top"]:
            lines.append(f"  - {item['code']} ({item['count']})")
    else:
        lines.append("- failed_reasons_top: []")
        lines.append("- failed_codes_top: []")
    return "\n".join(lines) + "\n"


def _build_dashboard_payload(summary: dict, *, alert_threshold: int) -> dict:
    has_alert = summary["policy_failures"] >= alert_threshold
    status = "warning" if has_alert else "ok"
    incidents = []
    if has_alert:
        incidents.append(
            {
                "event_name": "pass39_warning_summary_gate_policy",
                "status": "alert",
                "policy_failures": summary["policy_failures"],
                "failed_codes": summary["failed_codes_top"],
                "latest_total_reports": summary["total_reports"],
            }
        )
        for item in summary["failed_codes_top"]:
            incidents.append(
                {
                    "event_name": "pass39_warning_summary_gate_code_failure",
                    "status": "alert",
                    "code": item["code"],
                    "count": item["count"],
                }
            )
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "policy_failures": summary["policy_failures"],
        "latest_summary_records": summary["latest_summary_records"],
        "incidents": incidents,
    }


def _build_slack_payload(summary: dict, *, alert_threshold: int) -> dict:
    has_alert = summary["policy_failures"] >= alert_threshold
    if not has_alert:
        return {
            "text": "PASS-39 warning-summary gate is healthy",
            "blocks": [],
        }
    top_code = (
        summary["failed_codes_top"][0]["code"]
        if summary["failed_codes_top"]
        else "unknown"
    )
    return {
        "text": (
            f":warning: PASS-39 warning-summary gate has {summary['policy_failures']} "
            f"failed report(s), top code={top_code}"
        ),
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": (
                        f"warning-summary gate policy failures={summary['policy_failures']} "
                        f"recent_contexts={summary['recent_contexts']} "
                        f"latest_summary_records={summary['latest_summary_records']}"
                    ),
                },
            }
        ],
    }


def _build_monitoring_payload(
    summary: dict,
    *,
    alert_threshold: int,
    source: str = "agent-runtime-template",
) -> dict:
    has_alert = summary["policy_failures"] >= alert_threshold
    return {
        "schema_version": "agent-runtime.warning-summary-gate.monitoring-v1",
        "event_type": "pass39_warning_summary_gate_policy",
        "source": source,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "critical" if has_alert else "ok",
        "metrics": {
            "policy_failures": summary["policy_failures"],
            "total_reports": summary["total_reports"],
            "latest_summary_records": summary["latest_summary_records"],
            "recent_contexts": summary["recent_contexts"],
        },
        "alerts": {
            "active": has_alert,
            "alert_threshold": alert_threshold,
            "incident_count": len(summary["failed_codes_top"]),
        },
        "top_codes": summary["failed_codes_top"],
        "top_reasons": summary["failed_reasons_top"],
    }


def _looks_like_placeholder_or_invalid_url(url: str) -> tuple[bool, str]:
    value = (url or "").strip()
    if not value:
        return False, "empty"
    lower = value.lower()
    placeholder_markers = (
        "<",
        ">",
        "${",
        "{{",
        "}}",
        "placeholder",
        "changeme",
        "change.me",
        "todo",
        "example",
        "dummy",
        "your_url",
        "your-webhook",
        "xoxp-",
        "xoxb-",
    )
    if any(marker in lower for marker in placeholder_markers):
        return False, "contains placeholder marker"
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False, f"unsupported scheme: {parsed.scheme!r}"
    if not parsed.netloc:
        return False, "missing network location"
    return True, ""


def _validate_send_target(name: str, url: str) -> tuple[bool, str]:
    if not url:
        return False, "not configured"
    valid, detail = _looks_like_placeholder_or_invalid_url(url)
    if not valid:
        return False, f"{name} target invalid ({detail})"
    return True, ""


def _post_json(url: str, payload: dict, *, timeout_seconds: float) -> tuple[bool, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "agent-runtime-warning-summary-gate-summarizer",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = response.status if hasattr(response, "status") else response.getcode()
            body = response.read().decode("utf-8", errors="replace")
            if 200 <= status < 300:
                return True, body
            return False, f"HTTP {status}: {body}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return False, f"HTTP {exc.code}: {body}"
    except Exception as exc:
        return False, f"{exc.__class__.__name__}: {exc}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize warning-summary gate report.")
    parser.add_argument(
        "--path",
        default=os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH",
            ".tmp/template-warning-summary-gate-report.jsonl",
        ),
        help="Path to warning-summary gate JSONL report",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        help="Summarize only the last N report entries",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output summary as JSON.",
    )
    parser.add_argument(
        "--github-annotations",
        action="store_true",
        help="Emit GitHub Actions warning annotations for policy failures.",
    )
    parser.add_argument(
        "--fail-on-failures",
        action="store_true",
        help="Exit non-zero when policy failures are detected.",
    )
    parser.add_argument(
        "--dashboard-json",
        default="",
        help="Optional path to write alert-friendly dashboard payload.",
    )
    parser.add_argument(
        "--slack-payload",
        default="",
        help="Optional path to write Slack-formatted payload.",
    )
    parser.add_argument(
        "--alert-threshold",
        type=int,
        default=1,
        help="Policy failures at or above this count are alerted in dashboard payloads.",
    )
    parser.add_argument(
        "--monitoring-json",
        default="",
        help="Optional path to write monitoring ingestion payload.",
    )
    parser.add_argument(
        "--monitoring-source",
        default="agent-runtime-template",
        help="Label for monitoring payload `source` field.",
    )
    parser.add_argument(
        "--slack-webhook-url",
        default=os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_SLACK_WEBHOOK_URL",
            "",
        ),
        help="Optional Slack Incoming Webhook URL to POST slack payload.",
    )
    parser.add_argument(
        "--monitoring-endpoint-url",
        default=os.getenv(
            "PASS_39_WARNING_SUMMARY_GATE_MONITORING_ENDPOINT",
            "",
        ),
        help="Optional monitoring ingestion endpoint URL to POST monitoring payload.",
    )
    parser.add_argument(
        "--send-timeout",
        type=float,
        default=5.0,
        help="Timeout seconds used for webhook endpoint POST calls.",
    )
    parser.add_argument(
        "--send-on-ok",
        action="store_true",
        help="Send payloads even when policy failures are below threshold.",
    )
    parser.add_argument(
        "--fail-on-send-failures",
        action="store_true",
        help="Exit non-zero when any delivery attempt fails.",
    )
    parser.add_argument(
        "--slack-threshold",
        type=int,
        default=None,
        help="Minimum policy_failures required to send Slack payload (defaults to --alert-threshold).",
    )
    parser.add_argument(
        "--monitoring-threshold",
        type=int,
        default=None,
        help="Minimum policy_failures required to send monitoring payload (defaults to --alert-threshold).",
    )
    parser.add_argument(
        "--require-send-targets",
        action="store_true",
        help="Fail if should-send decision is true but no valid target exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build payloads and validate command inputs without sending HTTP requests.",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    report_records = _load_report_records(path)
    policy_failures, summary = _summarize(report_records, last=args.last)
    if args.github_annotations and policy_failures:
        for item in summary["failed_codes_top"]:
            print(
                f"::warning file={path.as_posix()}::"
                f"warning-summary gate policy failure count={item['count']} "
                f"code={item['code']}"
            )
    dashboard_payload = _build_dashboard_payload(summary, alert_threshold=args.alert_threshold)
    slack_payload = _build_slack_payload(summary, alert_threshold=args.alert_threshold)
    monitoring_payload = _build_monitoring_payload(
        summary,
        alert_threshold=args.alert_threshold,
        source=args.monitoring_source,
    )
    if args.dashboard_json:
        Path(args.dashboard_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.dashboard_json).write_text(
            json.dumps(dashboard_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.slack_payload:
        Path(args.slack_payload).parent.mkdir(parents=True, exist_ok=True)
        Path(args.slack_payload).write_text(
            json.dumps(slack_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.monitoring_json:
        Path(args.monitoring_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.monitoring_json).write_text(
            json.dumps(monitoring_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    failures = summary["policy_failures"]
    slack_threshold = (
        args.alert_threshold if args.slack_threshold is None else args.slack_threshold
    )
    monitoring_threshold = (
        args.alert_threshold
        if args.monitoring_threshold is None
        else args.monitoring_threshold
    )
    send_to_slack = args.send_on_ok or failures >= slack_threshold
    send_to_monitoring = args.send_on_ok or failures >= monitoring_threshold

    invalid_target_messages: list[str] = []
    send_failures: list[str] = []
    if send_to_slack and not args.dry_run:
        valid, reason = _validate_send_target("Slack", args.slack_webhook_url)
        if valid:
            ok, message = _post_json(
                args.slack_webhook_url,
                slack_payload,
                timeout_seconds=args.send_timeout,
            )
            if not ok:
                send_failures.append(f"slack-webhook: {message}")
            else:
                print(
                    f"Sent slack payload to {args.slack_webhook_url}",
                    file=sys.stderr,
                )
        else:
            invalid_target_messages.append(f"Slack target not used: {reason}")
    elif send_to_slack and args.dry_run:
        valid, reason = _validate_send_target("Slack", args.slack_webhook_url)
        if not valid:
            invalid_target_messages.append(f"Slack target not used: {reason}")

    if send_to_monitoring and not args.dry_run:
        valid, reason = _validate_send_target("monitoring", args.monitoring_endpoint_url)
        if valid:
            ok, message = _post_json(
                args.monitoring_endpoint_url,
                monitoring_payload,
                timeout_seconds=args.send_timeout,
            )
            if not ok:
                send_failures.append(f"monitoring-endpoint: {message}")
            else:
                print(
                    f"Sent monitoring payload to {args.monitoring_endpoint_url}",
                    file=sys.stderr,
                )
        else:
            invalid_target_messages.append(f"Monitoring target not used: {reason}")
    elif send_to_monitoring and args.dry_run:
        valid, reason = _validate_send_target("monitoring", args.monitoring_endpoint_url)
        if not valid:
            invalid_target_messages.append(f"Monitoring target not used: {reason}")

    if invalid_target_messages:
        print(f"Delivery skipped: {'; '.join(invalid_target_messages)}", file=sys.stderr)

    if args.require_send_targets:
        missing_valid = []
        valid, _ = _validate_send_target("Slack", args.slack_webhook_url)
        if send_to_slack and not valid:
            missing_valid.append("slack")
        valid, _ = _validate_send_target("monitoring", args.monitoring_endpoint_url)
        if send_to_monitoring and not valid:
            missing_valid.append("monitoring")
        if missing_valid:
            send_failures.append(
                f"missing valid send targets for alert mode: {', '.join(missing_valid)}"
            )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if invalid_target_messages:
            print(f"Delivery skipped: {'; '.join(invalid_target_messages)}", file=sys.stderr)
        if args.fail_on_send_failures and send_failures:
            print(f"Delivery failure(s): {', '.join(send_failures)}", file=sys.stderr)
            return 1
        return 1 if args.fail_on_failures and policy_failures else 0
    print(_render_text(summary), end="" if summary["total_reports"] else "\n")
    if invalid_target_messages:
        print(f"Delivery skipped: {'; '.join(invalid_target_messages)}", file=sys.stderr)
    if args.fail_on_send_failures and send_failures:
        print(f"Delivery failure(s): {', '.join(send_failures)}", file=sys.stderr)
        return 1
    return 1 if args.fail_on_failures and policy_failures else 0


if __name__ == "__main__":
    sys.exit(main())
