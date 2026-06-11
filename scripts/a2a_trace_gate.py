"""A2A trace reconstruction gate for agent_runtime.

Validates that request/review/decision/correction events can be reconstructed
with stable context/task identifiers, idempotency keys, retry policy, and access
control metadata.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("agents/project/a2a/a2a-trace-baseline-2026-06-09.jsonl")
DEFAULT_OUT = Path("reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json")

TRACE_SCHEMA_VERSION = "agent-runtime-a2a-envelope/v1"
MESSAGE_SCHEMA_VERSION = "agent-runtime-a2a-message/v1"
VALID_SCHEMA_VERSIONS = {TRACE_SCHEMA_VERSION, MESSAGE_SCHEMA_VERSION}
REQUIRED_EVENT_TYPES = ["request", "review", "decision", "correction"]
REQUIRED_FIELDS = [
    "schema_version",
    "event_id",
    "contextId",
    "taskId",
    "decision_cycle_id",
    "event_type",
    "sender",
    "receiver",
    "timestamp",
    "access_level",
    "idempotency_key",
    "retry_policy",
    "payload_ref",
]


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return rows, [f"missing:{path.as_posix()}"]
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"json-invalid:{path.as_posix()}:{idx}:{exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"json-not-object:{path.as_posix()}:{idx}")
            continue
        rows.append(value)
    return rows, errors


def _validate_retry_policy(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["retry_policy:not-object"]
    findings: list[str] = []
    if "retry_after" not in value:
        findings.append("retry_policy:missing-retry_after")
    if "max_retries" not in value:
        findings.append("retry_policy:missing-max_retries")
    else:
        try:
            if int(value["max_retries"]) < 0:
                findings.append("retry_policy:max_retries-negative")
        except Exception:  # noqa: BLE001
            findings.append("retry_policy:max_retries-not-int")
    if "reason_code" not in value:
        findings.append("retry_policy:missing-reason_code")
    return findings


def _validate_message_route(row: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if not row.get("message_id"):
        findings.append("missing:message_id")

    route = row.get("route")
    if not isinstance(route, dict):
        findings.append("missing:route")
    else:
        if route.get("from") != row.get("sender"):
            findings.append("invalid:route.from")
        if route.get("to") != row.get("receiver"):
            findings.append("invalid:route.to")

    task_context = row.get("task_context")
    if not isinstance(task_context, dict):
        findings.append("missing:task_context")
    else:
        for field in ("contextId", "taskId", "decision_cycle_id"):
            if task_context.get(field) != row.get(field):
                findings.append(f"invalid:task_context.{field}")
    return findings


def _validate_event(row: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            findings.append(f"missing:{field}")
    schema_version = row.get("schema_version")
    if schema_version not in VALID_SCHEMA_VERSIONS:
        findings.append("invalid:schema_version")
    findings.extend(_validate_retry_policy(row.get("retry_policy")))
    if row.get("event_type") not in REQUIRED_EVENT_TYPES:
        findings.append("invalid:event_type")
    if row.get("access_level") not in {"public", "project", "restricted", "owner-required"}:
        findings.append("invalid:access_level")
    if schema_version == MESSAGE_SCHEMA_VERSION:
        findings.extend(_validate_message_route(row))
    return findings


def _validate_message_chain(ordered: list[dict[str, Any]]) -> list[str]:
    if not ordered:
        return []
    if any(event.get("schema_version") != MESSAGE_SCHEMA_VERSION for event in ordered):
        return []
    findings: list[str] = []
    for previous, current in zip(ordered, ordered[1:]):
        previous_id = str(previous.get("event_id") or "")
        current_type = str(current.get("event_type") or "unknown")
        if str(current.get("parent_event_id") or "") != previous_id:
            findings.append(f"message-parent-link:{current_type}")
        if current.get("sender") != previous.get("receiver"):
            findings.append(f"message-route-handoff:{current_type}")
    return findings


def evaluate(input_path: Path) -> dict[str, Any]:
    rows, load_errors = _load_jsonl(input_path)
    findings = list(load_errors)
    event_ids: set[str] = set()
    idempotency: set[str] = set()
    by_chain: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    event_results: list[dict[str, Any]] = []

    for row in rows:
        event_id = str(row.get("event_id") or "unknown")
        row_findings = _validate_event(row)
        if event_id in event_ids:
            row_findings.append("duplicate:event_id")
        event_ids.add(event_id)
        key = str(row.get("idempotency_key") or "")
        if key:
            if key in idempotency:
                row_findings.append("duplicate:idempotency_key")
            idempotency.add(key)
        chain_key = (
            str(row.get("contextId") or ""),
            str(row.get("taskId") or ""),
            str(row.get("decision_cycle_id") or ""),
        )
        by_chain[chain_key].append(row)
        if row_findings:
            findings.extend(f"{event_id}:{item}" for item in row_findings)
        event_results.append({"event_id": event_id, "findings": row_findings})

    chain_results: list[dict[str, Any]] = []
    for chain_key, events in by_chain.items():
        context_id, task_id, decision_cycle_id = chain_key
        chain_findings: list[str] = []
        for required in REQUIRED_EVENT_TYPES:
            if required not in [str(event.get("event_type")) for event in events]:
                chain_findings.append(f"missing-event-type:{required}")
        ordered = sorted(events, key=lambda event: str(event.get("timestamp") or ""))
        ordered_types = [str(event.get("event_type")) for event in ordered]
        if [event.get("event_type") for event in ordered] != [event.get("event_type") for event in events]:
            chain_findings.append("events-not-timestamp-ordered")
        if ordered_types != REQUIRED_EVENT_TYPES:
            chain_findings.append("events-not-required-order")
        chain_findings.extend(_validate_message_chain(ordered))
        if chain_findings:
            findings.extend(f"{context_id}/{task_id}/{decision_cycle_id}:{item}" for item in chain_findings)
        chain_results.append(
            {
                "contextId": context_id,
                "taskId": task_id,
                "decision_cycle_id": decision_cycle_id,
                "event_types": ordered_types,
                "schema_versions": sorted({str(event.get("schema_version") or "") for event in events}),
                "findings": chain_findings,
            }
        )

    status = "pass" if rows and not findings else "block"
    message_events = [row for row in rows if row.get("schema_version") == MESSAGE_SCHEMA_VERSION]
    return {
        "schema": "agent-runtime-a2a-trace-gate/v1",
        "evaluation_mode": "a2a_trace_reconstruction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": input_path.as_posix(),
        "status": status,
        "events": len(rows),
        "message_events": len(message_events),
        "chains": len(chain_results),
        "findings": findings,
        "event_results": event_results,
        "chain_results": chain_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} events={report['events']} chains={report['chains']} out={args.out.as_posix()}")
    for chain in report["chain_results"]:
        print(
            f"{chain['contextId']}/{chain['taskId']}/{chain['decision_cycle_id']} "
            f"events={','.join(chain['event_types'])} findings={len(chain['findings'])}"
        )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
