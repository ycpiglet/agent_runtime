from __future__ import annotations

import builtins
import json
import os
import queue
import importlib.util
import time
import sys
import warnings
from datetime import datetime, timezone
from multiprocessing import Event, Process, Queue
from concurrent.futures import ThreadPoolExecutor
import threading
import uuid
from pathlib import Path
import re
from collections import Counter

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MESSAGE_QUEUE = REPO_ROOT / "src/agent_runtime/templates/project/scripts/message_queue.py"


class _Pass39LatencyRunIdRejectionLogWarning(RuntimeWarning):
    code = "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"

    def __init__(self, *, reason: str, log_path: str, error: str):
        super().__init__(reason)
        self.reason = reason
        self.log_path = log_path
        self.error = error


def _summarize_pass39_warning_codes(
    captured_warnings: list[warnings.WarningMessage],
) -> dict[str, int]:
    summary: dict[str, int] = {}
    for item in captured_warnings:
        raw = item.message
        if hasattr(raw, "code"):
            summary[str(raw.code)] = summary.get(str(raw.code), 0) + 1
    return summary


def _build_pass39_warning_summary_record(
    warning_code_counts: dict[str, int],
    *,
    total_warnings: int,
    run_id: str,
    event_name: str,
    window_start: str,
    window_end: str,
) -> dict[str, object]:
    return {
        "schema_version": "pass39-warning-summary-v1",
        "warning_code_counts": warning_code_counts,
        "total_warnings": total_warnings,
        "run_id": run_id,
        "event_name": event_name,
        "window_start": window_start,
        "window_end": window_end,
    }


def _evaluate_warning_summary_policy(
    records: list[dict[str, object]],
    *,
    max_warnings_per_context: int,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for record in records:
        run_id = record.get("run_id", "unknown")
        event_name = record.get("event_name", "unknown")
        warning_count = int(record.get("total_warnings", 0))
        if warning_count > max_warnings_per_context:
            reasons.append(
                f"context(run_id={run_id}, event={event_name}) has "
                f"{warning_count} warnings (max {max_warnings_per_context})"
            )
    return len(reasons) == 0, reasons


def _coalesce_warning_summary_records(
    records: list[dict[str, object]]
) -> list[dict[str, object]]:
    def _safe_int(value: object, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _parse_window_range(window_value: object) -> tuple[str, str]:
        if not isinstance(window_value, str):
            return "", ""
        split_parts = window_value.split("/")
        if len(split_parts) != 2:
            return "", ""
        start, end = split_parts[0].strip(), split_parts[1].strip()
        if not start or not end:
            return "", ""
        return start, end

    coalesced: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for record in records:
        schema_version = str(
            record.get("schema_version", "pass39-warning-summary-v1")
        )
        run_id = str(record.get("run_id", record.get("run", "legacy")))
        event_name = str(
            record.get("event_name", record.get("event", "legacy"))
        )
        window_start = record.get("window_start", record.get("ts_window_start"))
        window_end = record.get("window_end", record.get("window_end_time"))
        if (window_start in (None, "")) and (window_end in (None, "")):
            window_start, window_end = _parse_window_range(record.get("window"))
        window_start = str(window_start if window_start not in (None, "") else "")
        window_end = str(window_end if window_end not in (None, "") else "")
        key = (
            run_id,
            event_name,
            window_start,
            window_end,
        )
        if key not in coalesced:
            coalesced[key] = {
                "run_id": run_id,
                "event_name": event_name,
                "window_start": window_start,
                "window_end": window_end,
                "schema_version": schema_version,
                "warning_code_counts": dict(record.get("warning_code_counts", {})),
                "total_warnings": _safe_int(record.get("total_warnings", 0), 0),
            }
            continue

        existing = coalesced[key]
        existing_counts = dict(existing.get("warning_code_counts", {}))
        for code, count in dict(record.get("warning_code_counts", {})).items():
            existing_counts[code] = max(
                _safe_int(existing_counts.get(code, 0), 0),
                _safe_int(count, 0),
            )
        existing["warning_code_counts"] = existing_counts
        existing["total_warnings"] = max(
            _safe_int(existing.get("total_warnings", 0), 0),
            _safe_int(record.get("total_warnings", 0), 0),
        )

        # keep newest schema version if one record carries a higher generation
        if schema_version != existing["schema_version"]:
            existing["schema_version"] = schema_version

    return list(coalesced.values())


def _load_message_queue():
    return _load_message_queue_from_path(MESSAGE_QUEUE)


def _load_message_queue_from_path(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"message_queue_test_{uuid.uuid4().hex}",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _multiprocess_claim_worker(
    message_path: str,
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    start_event: Event,
    out: Queue,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    path = Path(message_path)
    start_event.wait()
    txt = path.read_text(encoding="utf-8")
    meta, body = module.parse_frontmatter(txt)
    out.put(module.claim_message(path, meta, body, role=role))


def _multiprocess_recover_and_claim_worker(
    message_path: str,
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    start_event: Event,
    out: Queue,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    path = Path(message_path)
    start_event.wait()
    try:
        module.recover_stale_claim(path)
        txt = path.read_text(encoding="utf-8")
        meta, body = module.parse_frontmatter(txt)
        out.put(module.claim_message(path, meta, body, role=role))
    except Exception:
        out.put(False)


def _multiprocess_recover_and_claim_worker_with_clock_skew(
    message_path: str,
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    now_override: float,
    start_event: Event,
    out: Queue,
    delay_seconds: float,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    module._now_epoch = lambda: now_override
    path = Path(message_path)
    start_event.wait()
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    try:
        module.recover_stale_claim(path, now=now_override)
        txt = path.read_text(encoding="utf-8")
        meta, body = module.parse_frontmatter(txt)
        out.put(module.claim_message(path, meta, body, role=role))
    except Exception:
        out.put(False)


def _multiprocess_stale_recover_worker(
    message_paths: list[str],
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    now_override: float,
    start_event: Event,
    out: Queue,
    pre_delay_seconds: float,
    post_delay_seconds: float,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    module._now_epoch = lambda: now_override
    paths = [Path(p) for p in message_paths]
    start_event.wait()
    if pre_delay_seconds > 0:
        time.sleep(pre_delay_seconds)
    for path in paths:
        try:
            module.recover_stale_claim(path, now=now_override)
            raw = path.read_text(encoding="utf-8")
            meta, body = module.parse_frontmatter(raw)
            if not module.claim_message(path, meta, body, role=role):
                out.put((str(path), False))
                continue
            if post_delay_seconds > 0:
                time.sleep(post_delay_seconds)
            reply = module.MESSAGES_INBOX / f"{path.stem}-worker-{module.os.getpid()}.reply.md"
            reply.write_text(
                "\n".join([
                    "---",
                    f"id: {reply.stem}",
                    "from: qa",
                    "to: orchestrator",
                    "type: reply",
                    "status: complete",
                    f"in_reply_to: {meta['id']}",
                    "---",
                    "ok",
                    "",
                ]),
                encoding="utf-8",
            )
            ok = module.mark_answered(path, role=role)
            out.put((str(path), ok))
        except Exception:
            out.put((str(path), False))


def _multiprocess_stale_recover_and_answer_worker(
    message_path: str,
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    now_override: float,
    start_event: Event,
    out: Queue,
    pre_delay_seconds: float,
    post_delay_seconds: float,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    module._now_epoch = lambda: now_override
    path = Path(message_path)
    start_event.wait()
    if pre_delay_seconds > 0:
        time.sleep(pre_delay_seconds)
    try:
        module.recover_stale_claim(path, now=now_override)
        raw = path.read_text(encoding="utf-8")
        meta, body = module.parse_frontmatter(raw)
        if not module.claim_message(path, meta, body, role=role):
            out.put((str(path), False))
            return
        if post_delay_seconds > 0:
            time.sleep(post_delay_seconds)
        reply = module.MESSAGES_INBOX / f"{path.stem}-worker-{module.os.getpid()}.reply.md"
        reply.write_text(
            "\n".join([
                "---",
                f"id: {reply.stem}",
                "from: qa",
                "to: orchestrator",
                "type: reply",
                "status: complete",
                f"in_reply_to: {meta['id']}",
                "---",
                "ok",
                "",
            ]),
            encoding="utf-8",
        )
        ok = module.mark_answered(path, role=role)
        out.put((str(path), ok))
    except Exception:
        out.put((str(path), False))


def _multiprocess_timed_stale_recover_and_answer_worker(
    message_path: str,
    module_path: str,
    messages_inbox: str,
    runtime_dir: str,
    role: str,
    now_override: float,
    start_event: Event,
    out: Queue,
    pre_delay_seconds: float,
    post_delay_seconds: float,
) -> None:
    module = _load_message_queue_from_path(Path(module_path))
    module.MESSAGES_INBOX = Path(messages_inbox)
    module.RUNTIME_DIR = Path(runtime_dir)
    module.CLAIMS_DIR = module.RUNTIME_DIR / "claims"
    module._now_epoch = lambda: now_override
    path = Path(message_path)
    start_event.wait()
    if pre_delay_seconds > 0:
        time.sleep(pre_delay_seconds)

    started = time.perf_counter()
    try:
        module.recover_stale_claim(path, now=now_override)
        raw = path.read_text(encoding="utf-8")
        meta, body = module.parse_frontmatter(raw)
        if not module.claim_message(path, meta, body, role=role):
            out.put((str(path), False, None))
            return
        if post_delay_seconds > 0:
            time.sleep(post_delay_seconds)
        reply = module.MESSAGES_INBOX / f"{path.stem}-worker-{module.os.getpid()}.reply.md"
        reply.write_text(
            "\n".join([
                "---",
                f"id: {reply.stem}",
                "from: qa",
                "to: orchestrator",
                "type: reply",
                "status: complete",
                f"in_reply_to: {meta['id']}",
                "---",
                "ok",
                "",
            ]),
            encoding="utf-8",
        )
        ok = module.mark_answered(path, role=role)
        elapsed_ms = (time.perf_counter() - started) * 1000
        out.put((str(path), ok, elapsed_ms))
    except Exception:
        out.put((str(path), False, None))


def _percentile_ms(values_ms: list[float], q: float) -> float:
    assert values_ms
    if not values_ms:
        return 0.0
    if q <= 0:
        return values_ms[0]
    if q >= 1:
        return values_ms[-1]
    position = q * (len(values_ms) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values_ms) - 1)
    lower = values_ms[lower_index]
    upper = values_ms[upper_index]
    if lower_index == upper_index or position.is_integer():
        return lower
    return lower + (upper - lower) * (position - lower_index)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"env {name} must be numeric, got: {value!r}") from exc


def _env_int(name: str, default: int | None) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"env {name} must be integer, got: {value!r}") from exc


def _maybe_write_latency_metrics(
    path: str,
    *,
    winner_latency_ms: list[float],
    failure_count: int,
    worker_count: int,
    total_messages: int,
    thresholds: dict[str, float],
    p95_ms: float,
    p99_ms: float,
    max_ms: float,
    failure_ratio: float,
    warnings: list[str],
) -> None:
    if not path:
        return
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "schema_version": "pass39-latency-metrics-v1",
        "pass_id": "PASS-39",
        "run_id": _build_latency_metric_run_id(default_timestamp=created_at),
        "created_at": created_at,
        "total_messages": total_messages,
        "total_workers": worker_count,
        "succeeded_workers": worker_count - failure_count,
        "failure_count": failure_count,
        "failure_ratio": failure_ratio,
        "metrics": {
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "max_ms": max_ms,
            "winner_count": len(winner_latency_ms),
            "winner_latency_ms": winner_latency_ms,
        },
        "thresholds": thresholds,
        "warnings": warnings,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".jsonl":
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    else:
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _assert_latency_metric_payload(payload: dict[str, object]) -> None:
    assert payload["schema_version"] == "pass39-latency-metrics-v1"
    assert payload["pass_id"] == "PASS-39"
    assert payload["run_id"]
    assert payload["created_at"]
    assert payload["total_messages"] > 0
    assert payload["total_workers"] > 0
    assert payload["succeeded_workers"] >= 0
    metrics = payload["metrics"]
    assert isinstance(metrics, dict)
    assert metrics["winner_count"] >= 1
    assert "p95_ms" in metrics
    assert "p99_ms" in metrics
    assert isinstance(payload["warnings"], list)


def _load_latency_metric_records(path: str) -> list[dict[str, object]]:
    output_path = Path(path)
    if not str(path).strip():
        return []
    if not output_path.exists():
        return []
    if output_path.suffix.lower() == ".jsonl":
        records: list[dict[str, object]] = []
        for raw in output_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            records.append(json.loads(line))
        return records

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return [payload] if isinstance(payload, dict) else []


def _summarize_latency_metric_records(
    records: list[dict[str, object]],
) -> dict[str, object]:
    warning_records = [record for record in records if record.get("warnings")]
    warning_counts = [len(record.get("warnings", [])) for record in records]
    return {
        "records": len(records),
        "warning_records": len(warning_records),
        "max_warning_count": max(warning_counts, default=0),
        "failed_records": [record.get("run_id") for record in warning_records],
        "all_ok": len(warning_records) == 0,
    }


def _evaluate_latency_policy(
    records: list[dict[str, object]],
    policy_mode: str,
    *,
    max_warning_count: int | None = None,
) -> tuple[bool, dict[str, object]]:
    summary = _summarize_latency_metric_records(records)
    reason: list[str] = []

    if policy_mode == "fail-on-warning":
        if summary["warning_records"]:
            reason.append("warning_records exists but fail-on-warning is active")
    if max_warning_count is not None and max_warning_count > 0 and (
        summary["max_warning_count"] > max_warning_count
    ):
        reason.append(
            f"max_warning_count > {max_warning_count} "
            f"({summary['max_warning_count']} > {max_warning_count})"
        )

    passed = len(reason) == 0
    return passed, {"summary": summary, "reason": reason, "policy_mode": policy_mode}


def _policy_mode_from_env(default: str = "warning-only") -> str:
    mode = os.getenv("PASS_39_LATENCY_POLICY", default).strip()
    if mode in {"warning-only", "fail-on-warning"}:
        return mode
    return default


def _append_jsonl_record(path: str, payload: object) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _expected_ci_run_id_patterns(run_id: str) -> str:
    return (
        f"run-{run_id}-<event>-py<python>-warning | "
        f"run-{run_id}-<event>-main-py<python>-fail-<sha> | "
        f"run-{run_id}-<event>-schedule-py<python>-fail"
    )


def _expected_mode_for_run_id(run_id: str) -> str:
    if not run_id.startswith("run-"):
        return "manual"
    if (
        " " in run_id
        or "\n" in run_id
        or "\r" in run_id
        or "\t" in run_id
    ):
        return "manual"
    return "ci"


def test_latency_metric_helpers_respect_env_overrides_and_emit_artifact(tmp_path, monkeypatch):
    assert _env_float("PASS_39_MAX_P95_MS", 2500.0) == 2500.0
    monkeypatch.setenv("PASS_39_MAX_P95_MS", "1234.5")
    assert _env_float("PASS_39_MAX_P95_MS", 2500.0) == 1234.5
    monkeypatch.setenv("PASS_39_MAX_P95_MS", "")
    assert _env_float("PASS_39_MAX_P95_MS", 2500.0) == 2500.0

    output = tmp_path / "latency-metrics.json"
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[10.0, 20.0, 30.0],
        failure_count=1,
        worker_count=8,
        total_messages=3,
        thresholds={
            "max_p95_ms": 1234.5,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=20.0,
        p99_ms=30.0,
        max_ms=30.0,
        failure_ratio=0.125,
        warnings=[],
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    _assert_latency_metric_payload(payload)
    assert payload["thresholds"]["max_p95_ms"] == 1234.5


def test_latency_metric_artifact_supports_jsonl_schema(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics.jsonl"
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "RUN-2026-06-09-pass39")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[5.0, 25.0],
        failure_count=2,
        worker_count=4,
        total_messages=2,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=16.0,
        p99_ms=20.0,
        max_ms=25.0,
        failure_ratio=0.5,
        warnings=["jsonl sample warning"],
    )
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[7.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=7.0,
        p99_ms=7.0,
        max_ms=7.0,
        failure_ratio=0.0,
        warnings=[],
    )
    lines = [line.strip() for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    first, second = [json.loads(line) for line in lines]
    _assert_latency_metric_payload(first)
    _assert_latency_metric_payload(second)
    assert first["run_id"] == "RUN-2026-06-09-pass39"


def test_latency_metric_invalid_run_id_is_rejected(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-invalid-run-id.jsonl"
    rejection_log = tmp_path / "artifacts" / "run-id-rejection.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run-2026 06-09")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[4.0, 6.0],
            failure_count=1,
            worker_count=2,
            total_messages=2,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=16.0,
            p99_ms=18.0,
            max_ms=18.0,
            failure_ratio=0.5,
            warnings=[],
        )
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[5.0],
        failure_count=0,
        worker_count=1,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=5.0,
        p99_ms=5.0,
        max_ms=5.0,
        failure_ratio=0.0,
        warnings=[],
    )
    record = json.loads(output.read_text(encoding="utf-8").splitlines()[-1])
    assert _ISO8601_RE.fullmatch(record["run_id"]) is not None
    lines = [
        line.strip()
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1
    rejection = json.loads(lines[0])
    assert rejection["kind"] == "pass39-latency-metrics-run-id-rejection"
    assert rejection["run_id"] == "run-2026 06-09"
    assert rejection["reason"] == "PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"
    assert "no-whitespace" in rejection["expected_pattern"]
    assert rejection["expected_mode"] == "manual"


def test_latency_metric_rejection_log_smoke_path(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-smoke.jsonl"
    rejection_log = tmp_path / ".tmp" / "pass39-latency-metrics-run-id-rejections.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 123456")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[4.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=11.0,
            p99_ms=11.0,
            max_ms=11.0,
            failure_ratio=0.0,
            warnings=[],
        )
    entries = [
        json.loads(line)
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    rejection = entries[0]
    assert rejection["schema_version"] == "pass39-latency-run-id-rejection-v1"
    assert rejection["expected_pattern"].startswith("run-id must be no-whitespace")
    assert Path(rejection["rejection_log_path"]).name == "pass39-latency-metrics-run-id-rejections.jsonl"


def test_latency_run_id_rejection_modes_are_aggregatable(tmp_path, monkeypatch):
    rejection_log = tmp_path / "artifacts" / "run-id-mode-summary.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )
    run_id_cases = {
        "run-abc-push-py3.10-warning": "ci",
        "run-xyz-schedule-py3.12-fail": "ci",
        "manual-case-1": "manual",
        "run-no-space value": "manual",
        "run-9999-main-py3.11-fail-nohash": "ci",
    }
    expected_mode_counts = Counter(run_id_cases.values())

    for run_id in run_id_cases:
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", run_id)
        expected_mode = run_id_cases[run_id]
        if expected_mode == "manual":
            with pytest.raises(ValueError):
                _maybe_write_latency_metrics(
                    str(tmp_path / "artifacts" / "mode-summary-target.jsonl"),
                    winner_latency_ms=[1.0],
                    failure_count=0,
                    worker_count=1,
                    total_messages=1,
                    thresholds={
                        "max_p95_ms": 2500.0,
                        "max_p99_ms": 3500.0,
                        "max_failure_ratio": 0.85,
                    },
                    p95_ms=1.0,
                    p99_ms=1.0,
                    max_ms=1.0,
                    failure_ratio=0.0,
                    warnings=[],
                )
        else:
            with pytest.raises(ValueError, match="must follow CI pattern"):
                _maybe_write_latency_metrics(
                    str(tmp_path / "artifacts" / "mode-summary-target.jsonl"),
                    winner_latency_ms=[1.0],
                    failure_count=0,
                    worker_count=1,
                    total_messages=1,
                    thresholds={
                        "max_p95_ms": 2500.0,
                        "max_p99_ms": 3500.0,
                        "max_failure_ratio": 0.85,
                    },
                    p95_ms=1.0,
                    p99_ms=1.0,
                    max_ms=1.0,
                    failure_ratio=0.0,
                    warnings=[],
                )

    entries = [
        json.loads(line)
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    entries_by_run_id = {entry["run_id"]: entry for entry in entries}
    assert len(entries_by_run_id) == len(run_id_cases)
    assert len(entries) == len(run_id_cases)
    mode_counts = Counter(entry["expected_mode"] for entry in entries)
    for run_id, expected_mode in run_id_cases.items():
        assert entries_by_run_id[run_id]["expected_mode"] == expected_mode
        assert entries_by_run_id[run_id]["expected_pattern"] in {
            "run-id must be no-whitespace and follow run-* CI patterns or manual-*",
            "run-<run-id>-<event>-py<python>-warning | "
            "run-<run-id>-<event>-main-py<python>-fail-<sha> | "
            "run-<run-id>-<event>-schedule-py<python>-fail",
        }
    assert mode_counts == expected_mode_counts


def test_latency_rejection_log_and_policy_thresholds_are_observably_correlated(
    tmp_path,
    monkeypatch,
):
    rejection_log = tmp_path / "artifacts" / ".tmp" / "pass39-latency-metrics-run-id-rejections.jsonl"
    output = tmp_path / "artifacts" / "policy-rejection-correlation.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )
    monkeypatch.setenv("PASS_39_LATENCY_POLICY", "warning-only")
    monkeypatch.setenv("PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT", "1")
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_PATH", str(output))

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run has space 2026")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[1.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=1.0,
            p99_ms=1.0,
            max_ms=1.0,
            failure_ratio=0.0,
            warnings=[],
        )

    entries = [
        json.loads(line)
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["expected_mode"] == "manual"
    assert Path(entries[0]["rejection_log_path"]).parent.name == ".tmp"
    assert Path(entries[0]["rejection_log_path"]).name == "pass39-latency-metrics-run-id-rejections.jsonl"

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "manual-2026-06-09-policy")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[2.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=2.0,
        p99_ms=2.0,
        max_ms=2.0,
        failure_ratio=0.0,
        warnings=["warn-1"],
    )
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[3.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=3.0,
        p99_ms=3.0,
        max_ms=3.0,
        failure_ratio=0.0,
        warnings=["warn-1", "warn-2"],
    )

    records = _load_latency_metric_records(str(output))
    policy_mode = _policy_mode_from_env()
    max_warning_count = _env_int("PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT", None)
    assert max_warning_count == 1
    passed, report = _evaluate_latency_policy(
        records,
        policy_mode,
        max_warning_count=max_warning_count,
    )
    assert passed is False
    assert report["policy_mode"] == "warning-only"
    assert report["summary"]["max_warning_count"] == 2
    assert any("max_warning_count > 1" in item for item in report["reason"])

    monkeypatch.setenv("PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT", "2")
    max_warning_count = _env_int("PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT", None)
    assert max_warning_count == 2
    passed, report = _evaluate_latency_policy(
        records,
        policy_mode,
        max_warning_count=max_warning_count,
    )
    assert passed is True
    assert report["policy_mode"] == "warning-only"
    assert report["reason"] == []


def test_latency_run_id_rejection_log_path_empty_skips_logging(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-empty-log.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        "",
    )

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run-abc 2026")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[4.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=10.0,
            p99_ms=10.0,
            max_ms=10.0,
            failure_ratio=0.0,
            warnings=[],
        )

    default_candidate = tmp_path / ".tmp" / "pass39-latency-metrics-run-id-rejections.jsonl"
    assert not default_candidate.exists()
    assert not output.exists()


def test_latency_run_id_rejection_log_path_preserves_custom_destination(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-custom-path.jsonl"
    rejection_log = tmp_path / "artifacts" / "audit" / "run-id-rejections.logl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 123-abc")

    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[5.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=5.0,
            p99_ms=5.0,
            max_ms=5.0,
            failure_ratio=0.0,
            warnings=[],
        )

    entries = [
        json.loads(line)
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["rejection_log_path"] == str(rejection_log)
    assert entries[0]["expected_mode"] == "manual"


def test_latency_run_id_rejection_log_path_works_with_relative_path(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-relative-path.jsonl"
    relative = Path("artifacts") / "audit" / "run-id-rejections.logl"
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH", str(relative))
    (tmp_path / "artifacts" / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 2026 relative")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[6.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=6.0,
            p99_ms=6.0,
            max_ms=6.0,
            failure_ratio=0.0,
            warnings=[],
        )

    resolved_path = tmp_path / relative
    entries = [
        json.loads(line)
        for line in resolved_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["rejection_log_path"] == str(relative)
    assert entries[0]["run_id"] == "run 2026 relative"


@pytest.mark.parametrize(
    "rejection_log_path",
    [
        "artifacts/audit/run-id-rejections%0A.logl",
        "artifacts/audit space/run-id-rejections.logl",
    ],
)
def test_latency_run_id_rejection_log_path_preserves_encoded_or_spaced_input(
    tmp_path,
    monkeypatch,
    rejection_log_path: str,
):
    output = tmp_path / "artifacts" / "latency-metrics-encoded-path.jsonl"
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH", rejection_log_path)
    (tmp_path / "artifacts" / "audit").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    (tmp_path / Path(rejection_log_path).parent).mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 2026 encoded")
    with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"):
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[7.0],
            failure_count=0,
            worker_count=1,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=7.0,
            p99_ms=7.0,
            max_ms=7.0,
            failure_ratio=0.0,
            warnings=[],
        )

    resolved = tmp_path / rejection_log_path
    assert resolved.exists()
    entries = [
        json.loads(line)
        for line in resolved.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["rejection_log_path"] == rejection_log_path


def test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection(
    tmp_path,
    monkeypatch,
):
    output = tmp_path / "artifacts" / "latency-metrics-write-fail.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(tmp_path / ".tmp" / "unwritable" / "run-id-rejections.logl"),
    )
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 2026 write-fail")
    failure = {"count": 0}

    def _failing_append(path: str, payload: object) -> None:
        failure["count"] += 1
        raise PermissionError("simulated unwritable path")

    monkeypatch.setattr(sys.modules[__name__], "_append_jsonl_record", _failing_append)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        with pytest.raises(
            ValueError,
            match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace",
        ):
            _maybe_write_latency_metrics(
                str(output),
                winner_latency_ms=[9.0],
                failure_count=0,
                worker_count=1,
                total_messages=1,
                thresholds={
                    "max_p95_ms": 2500.0,
                    "max_p99_ms": 3500.0,
                    "max_failure_ratio": 0.85,
                },
                p95_ms=9.0,
                p99_ms=9.0,
                max_ms=9.0,
                failure_ratio=0.0,
                warnings=[],
            )

    assert len(captured) == 1
    warning = captured[0].message
    assert isinstance(warning, _Pass39LatencyRunIdRejectionLogWarning)
    assert warning.code == "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"
    assert "write failed" in warning.reason

    assert failure["count"] == 1
    assert not output.exists()


def test_latency_run_id_rejection_log_path_unwritable_warns_accumulate_across_failures(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-write-fail-multiple.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(tmp_path / ".tmp" / "unwritable" / "run-id-rejections.logl"),
    )

    failure = {"count": 0}

    def _failing_append(path: str, payload: object) -> None:
        failure["count"] += 1
        raise PermissionError("simulated unwritable path")

    monkeypatch.setattr(sys.modules[__name__], "_append_jsonl_record", _failing_append)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")

        for run_id in ["run 2026 write-fail-1", "run 2026 write-fail-2"]:
            monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", run_id)
            with pytest.raises(
                ValueError,
                match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace",
            ):
                _maybe_write_latency_metrics(
                    str(output),
                    winner_latency_ms=[9.0],
                    failure_count=0,
                    worker_count=1,
                    total_messages=1,
                    thresholds={
                        "max_p95_ms": 2500.0,
                        "max_failure_ratio": 0.85,
                        "max_p99_ms": 3500.0,
                    },
                    p95_ms=9.0,
                    p99_ms=9.0,
                    max_ms=9.0,
                    failure_ratio=0.0,
                    warnings=[],
                )

    assert failure["count"] == 2
    assert len(captured) == 2
    assert all(
        isinstance(item.message, _Pass39LatencyRunIdRejectionLogWarning)
        for item in captured
    )
    assert all(item.message.code == "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE" for item in captured)


def test_latency_run_id_rejection_warning_codes_are_aggregateable(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-write-fail-summary.jsonl"
    warning_summary_path = tmp_path / "artifacts" / "warning-summaries.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(tmp_path / ".tmp" / "unwritable" / "run-id-rejections.logl"),
    )
    monkeypatch.setenv("GITHUB_RUN_ID", "5555")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")

    def _failing_append(path: str, payload: object) -> None:
        raise PermissionError("simulated unwritable path")

    monkeypatch.setattr(sys.modules[__name__], "_append_jsonl_record", _failing_append)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "run 2026 summary-1")
        with pytest.raises(
            ValueError,
            match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace",
        ):
            _maybe_write_latency_metrics(
                str(output),
                winner_latency_ms=[10.0],
                failure_count=0,
                worker_count=1,
                total_messages=1,
                thresholds={
                    "max_p95_ms": 2500.0,
                    "max_p99_ms": 3500.0,
                    "max_failure_ratio": 0.85,
                },
                p95_ms=10.0,
                p99_ms=10.0,
                max_ms=10.0,
                failure_ratio=0.0,
                warnings=[],
            )

    summary = _summarize_pass39_warning_codes(captured)
    assert summary == {
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1,
    }

    warning_summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_payload = _build_pass39_warning_summary_record(
        summary,
        total_warnings=len(captured),
        run_id=os.getenv("GITHUB_RUN_ID", "manual"),
        event_name=os.getenv("GITHUB_EVENT_NAME", "manual"),
        window_start="2026-06-09T00:00:00Z",
        window_end="2026-06-09T00:01:00Z",
    )
    warning_summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    records = [
        json.loads(line)
        for line in warning_summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 1
    assert records[0]["schema_version"] == "pass39-warning-summary-v1"
    assert records[0]["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 1
    assert records[0]["run_id"] == "5555"
    assert records[0]["event_name"] == "pull_request"
    assert records[0]["window_start"] == "2026-06-09T00:00:00Z"
    assert records[0]["window_end"] == "2026-06-09T00:01:00Z"


def test_latency_run_id_rejection_warning_summary_is_partitioned_by_context(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-write-fail-context.jsonl"
    warning_summary_path = tmp_path / "artifacts" / "warning-summary-partitioned.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(tmp_path / ".tmp" / "unwritable" / "run-id-rejections.logl"),
    )

    def _failing_append(path: str, payload: object) -> None:
        raise PermissionError("simulated unwritable path")

    monkeypatch.setattr(sys.modules[__name__], "_append_jsonl_record", _failing_append)

    contexts = [
        {
            "run_id": "1001",
            "event_name": "push",
            "run_id_input": "run 2026 context-push",
            "window": ("2026-06-09T10:00:00Z", "2026-06-09T10:01:00Z"),
        },
        {
            "run_id": "1002",
            "event_name": "schedule",
            "run_id_input": "run 2026 context-schedule",
            "window": ("2026-06-09T10:05:00Z", "2026-06-09T10:06:00Z"),
        },
    ]

    summary_records: list[dict[str, object]] = []
    for context in contexts:
        monkeypatch.setenv("GITHUB_RUN_ID", context["run_id"])
        monkeypatch.setenv("GITHUB_EVENT_NAME", context["event_name"])
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", context["run_id_input"])

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            with pytest.raises(
                ValueError,
                match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace",
            ):
                _maybe_write_latency_metrics(
                    str(output),
                    winner_latency_ms=[12.0],
                    failure_count=0,
                    worker_count=1,
                    total_messages=1,
                    thresholds={
                        "max_p95_ms": 2500.0,
                        "max_p99_ms": 3500.0,
                        "max_failure_ratio": 0.85,
                    },
                    p95_ms=12.0,
                    p99_ms=12.0,
                    max_ms=12.0,
                    failure_ratio=0.0,
                    warnings=[],
                )

        summary = _summarize_pass39_warning_codes(captured)
        summary_records.append(
            _build_pass39_warning_summary_record(
                summary,
                total_warnings=len(captured),
                run_id=context["run_id"],
                event_name=context["event_name"],
                window_start=context["window"][0],
                window_end=context["window"][1],
            )
        )

    warning_summary_path.parent.mkdir(parents=True, exist_ok=True)
    warning_summary_path.write_text(
        "\n".join(
            [
                json.dumps(record, ensure_ascii=False)
                for record in summary_records
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    records = [
        json.loads(line)
        for line in warning_summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 2
    assert {record["run_id"] for record in records} == {"1001", "1002"}
    assert {record["event_name"] for record in records} == {"push", "schedule"}
    assert {
        record["window_start"] for record in records
    } == {"2026-06-09T10:00:00Z", "2026-06-09T10:05:00Z"}
    assert {
        (record["run_id"], record["event_name"]) for record in records
    } == {("1001", "push"), ("1002", "schedule")}
    assert all(
        record["warning_code_counts"].get("PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE") == 1
        for record in records
    )


def test_latency_warning_summary_policy_evaluation_is_context_aware(tmp_path):
    summary_path = tmp_path / "artifacts" / "warning-summary-policy.jsonl"
    summary_records = [
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 2},
            total_warnings=2,
            run_id="1001",
            event_name="push",
            window_start="2026-06-09T10:00:00Z",
            window_end="2026-06-09T10:01:00Z",
        ),
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1},
            total_warnings=1,
            run_id="1002",
            event_name="schedule",
            window_start="2026-06-09T10:05:00Z",
            window_end="2026-06-09T10:06:00Z",
        ),
    ]

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "\n".join(
            [json.dumps(record, ensure_ascii=False) for record in summary_records]
        )
        + "\n",
        encoding="utf-8",
    )
    records = [
        json.loads(line)
        for line in summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    passed, reasons = _evaluate_warning_summary_policy(
        records,
        max_warnings_per_context=1,
    )
    assert passed is False
    assert len(reasons) == 1
    assert "run_id=1001" in reasons[0]

    passed, reasons = _evaluate_warning_summary_policy(
        records,
        max_warnings_per_context=2,
    )
    assert passed is True
    assert reasons == []


def test_latency_warning_summary_records_are_coalesced_by_context(tmp_path):
    raw_records = [
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1},
            total_warnings=1,
            run_id="2001",
            event_name="push",
            window_start="2026-06-09T10:00:00Z",
            window_end="2026-06-09T10:01:00Z",
        ),
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 3},
            total_warnings=3,
            run_id="2001",
            event_name="push",
            window_start="2026-06-09T10:00:00Z",
            window_end="2026-06-09T10:01:00Z",
        ),
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 2},
            total_warnings=2,
            run_id="2002",
            event_name="schedule",
            window_start="2026-06-09T10:05:00Z",
            window_end="2026-06-09T10:06:00Z",
        ),
    ]

    coalesced = _coalesce_warning_summary_records(raw_records)
    assert len(coalesced) == 2
    run_event_count = {
        (record["run_id"], record["event_name"], record["window_start"], record["window_end"]): record
        for record in coalesced
    }
    merged_push = run_event_count[
        ("2001", "push", "2026-06-09T10:00:00Z", "2026-06-09T10:01:00Z")
    ]
    assert merged_push["total_warnings"] == 3
    assert merged_push["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 3

    merged_schedule = run_event_count[
        ("2002", "schedule", "2026-06-09T10:05:00Z", "2026-06-09T10:06:00Z")
    ]
    assert merged_schedule["total_warnings"] == 2
    assert merged_schedule["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 2

    evaluated, reasons = _evaluate_warning_summary_policy(
        coalesced,
        max_warnings_per_context=2,
    )
    assert evaluated is False
    assert len(reasons) == 1
    assert "run_id=2001" in reasons[0]


def test_latency_warning_summary_schema_compatibility_keeps_aggregation_stable(tmp_path):
    mixed_schema_records = [
        _build_pass39_warning_summary_record(
            {"PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1},
            total_warnings=1,
            run_id="3001",
            event_name="push",
            window_start="2026-06-09T10:00:00Z",
            window_end="2026-06-09T10:01:00Z",
        ),
        {
            "schema_version": "pass39-warning-summary-v0",
            "run": "3001",
            "event": "push",
            "window": "2026-06-09T10:00:00Z/2026-06-09T10:01:00Z",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 2
            },
            "total_warnings": 2,
        },
        {
            "schema_version": "pass39-warning-summary-legacy",
            "run_id": "3001",
            "event_name": "push",
            "window_start": "2026-06-09T10:00:00Z",
            "window_end": "2026-06-09T10:01:00Z",
            "warning_code_counts": {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            },
            "total_warnings": 1,
        },
    ]

    coalesced = _coalesce_warning_summary_records(mixed_schema_records)
    assert len(coalesced) == 1
    merged = coalesced[0]
    assert merged["run_id"] == "3001"
    assert merged["event_name"] == "push"
    assert merged["window_start"] == "2026-06-09T10:00:00Z"
    assert merged["window_end"] == "2026-06-09T10:01:00Z"
    assert merged["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 2
    assert merged["total_warnings"] == 2
    assert merged["schema_version"] == "pass39-warning-summary-legacy"

    passed, reasons = _evaluate_warning_summary_policy(
        coalesced,
        max_warnings_per_context=1,
    )
    assert passed is False
    assert "run_id=3001" in reasons[0]


def test_latency_warning_summary_schema_mixed_records_survive_end_to_end_write_read_and_policies(
    tmp_path, monkeypatch
):
    warning_summary_path = tmp_path / "artifacts" / "warning-summary-pipe-mixed-schema.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(tmp_path / ".tmp" / "run-id-rejections.logl"),
    )

    def _make_summary_payload(
        *,
        run_id: str,
        event_name: str,
        window_start: str,
        window_end: str,
        metrics_run_id: str,
    ) -> dict[str, object]:
        metrics_path = tmp_path / "artifacts" / f"latency-metrics-{run_id}.jsonl"
        monkeypatch.setenv("GITHUB_RUN_ID", run_id)
        monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", metrics_run_id)

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            with pytest.raises(
                ValueError,
                match="PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace",
            ):
                _maybe_write_latency_metrics(
                    str(metrics_path),
                    winner_latency_ms=[11.0],
                    failure_count=0,
                    worker_count=1,
                    total_messages=1,
                    thresholds={
                        "max_p95_ms": 2500.0,
                        "max_p99_ms": 3500.0,
                        "max_failure_ratio": 0.85,
                    },
                    p95_ms=11.0,
                    p99_ms=11.0,
                    max_ms=11.0,
                    failure_ratio=0.0,
                    warnings=[],
                )

        summary = _summarize_pass39_warning_codes(captured)
        if not summary:
            summary = {
                "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 1
            }
        return _build_pass39_warning_summary_record(
            summary,
            total_warnings=max(len(captured), 1),
            run_id=run_id,
            event_name=event_name,
            window_start=window_start,
            window_end=window_end,
        )

    warning_summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_push_v1 = _make_summary_payload(
        run_id="7001",
        event_name="push",
        window_start="2026-06-09T11:00:00Z",
        window_end="2026-06-09T11:01:00Z",
        metrics_run_id="run 2026 pass-75-push-1",
    )
    summary_push_v0 = dict(summary_push_v1)
    summary_push_v0["schema_version"] = "pass39-warning-summary-v0"
    summary_push_v0["run"] = summary_push_v0.pop("run_id")
    summary_push_v0["event"] = summary_push_v0.pop("event_name")
    summary_push_v0["window"] = (
        "2026-06-09T11:00:00Z/2026-06-09T11:01:00Z"
    )
    summary_push_v0["total_warnings"] = 3
    summary_push_v0["warning_code_counts"] = {
        "PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE": 3
    }

    summary_schedule = _make_summary_payload(
        run_id="7002",
        event_name="schedule",
        window_start="2026-06-09T11:05:00Z",
        window_end="2026-06-09T11:06:00Z",
        metrics_run_id="run 2026 pass-75-schedule",
    )
    summary_schedule["schema_version"] = "pass39-warning-summary-legacy"

    for payload in [summary_push_v1, summary_push_v0, summary_schedule]:
        _append_jsonl_record(str(warning_summary_path), payload)

    loaded_records = [
        json.loads(line)
        for line in warning_summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(loaded_records) == 3
    coalesced = _coalesce_warning_summary_records(loaded_records)
    assert len(coalesced) == 2

    key_by_context = {
        (record["run_id"], record["event_name"], record["window_start"], record["window_end"]): record
        for record in coalesced
    }
    merged_push = key_by_context[
        ("7001", "push", "2026-06-09T11:00:00Z", "2026-06-09T11:01:00Z")
    ]
    assert merged_push["schema_version"] == "pass39-warning-summary-v0"
    assert merged_push["total_warnings"] == 3
    assert merged_push["warning_code_counts"]["PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE"] == 3

    merged_schedule = key_by_context[
        ("7002", "schedule", "2026-06-09T11:05:00Z", "2026-06-09T11:06:00Z")
    ]
    assert merged_schedule["total_warnings"] == 1

    passed, reasons = _evaluate_warning_summary_policy(
        coalesced,
        max_warnings_per_context=2,
    )
    assert passed is False
    assert len(reasons) == 1
    assert "run_id=7001" in reasons[0]


def test_latency_metric_artifact_allows_ci_run_id_variants(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-runids.jsonl"
    run_id_variants = [
        "run-1234567890-push-py3.10-warning",
        "run-1234567890-push-main-py3.10-fail-deadbeefcafecafe",
        "run-1234567890-schedule-py3.10-fail",
    ]
    for idx, run_id in enumerate(run_id_variants, start=1):
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", run_id)
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[float(idx), float(idx + 1)],
            failure_count=idx % 2,
            worker_count=2,
            total_messages=2,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=10.0 + idx,
            p99_ms=12.0 + idx,
            max_ms=12.0 + idx,
            failure_ratio=0.1 * idx,
            warnings=[],
        )
    lines = [line.strip() for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    assert len(records) == len(run_id_variants)
    assert [record["run_id"] for record in records] == run_id_variants
    assert all(record["run_id"].startswith("run-") for record in records)
    assert all("-py3.10-" in record["run_id"] for record in records)
    assert records[0]["run_id"].endswith("-warning")
    assert "-main-" in records[1]["run_id"]
    assert records[1]["run_id"].startswith("run-1234567890")
    assert "-schedule-" in records[2]["run_id"]


def test_ci_workflow_latency_run_id_template_patterns_are_declared():
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )
    warning_pattern = (
        "run-${{ github.run_id }}-${{ github.event_name }}"
        "-py${{ matrix.python-version }}-warning"
    )
    main_pattern = (
        "run-${{ github.run_id }}-${{ github.event_name }}-main"
        "-py${{ matrix.python-version }}-fail-${{ github.sha }}"
    )
    schedule_pattern = (
        "run-${{ github.run_id }}-${{ github.event_name }}"
        "-schedule-py${{ matrix.python-version }}-fail"
    )
    assert warning_pattern in workflow
    assert main_pattern in workflow
    assert schedule_pattern in workflow
    for pattern in (warning_pattern, main_pattern, schedule_pattern):
        assert re.search(r"\$\{\{\s*github\.run_id\s*\}\}", pattern) is not None


def test_latency_run_id_patterns_differentiate_ci_and_manual_cases(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "latency-metrics-pattern-cases.jsonl"
    rejection_log = tmp_path / "artifacts" / "run-id-pattern-rejection.jsonl"
    monkeypatch.setenv(
        "PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH",
        str(rejection_log),
    )

    valid_run_ids = {
        "run-1234567890-push-py3.10-warning": "warning",
        "run-1234567890-push-main-py3.10-fail-deadbeefcafecafe": "main",
        "run-1234567890-schedule-py3.12-fail": "schedule",
    }
    for run_id, expected_mode in valid_run_ids.items():
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", run_id)
        _maybe_write_latency_metrics(
            str(output),
            winner_latency_ms=[11.0],
            failure_count=0,
            worker_count=2,
            total_messages=1,
            thresholds={
                "max_p95_ms": 2500.0,
                "max_p99_ms": 3500.0,
                "max_failure_ratio": 0.85,
            },
            p95_ms=11.0,
            p99_ms=11.0,
            max_ms=11.0,
            failure_ratio=0.0,
            warnings=[],
        )
        record = json.loads(output.read_text(encoding="utf-8").splitlines()[-1])
        assert _classify_latency_run_id(record["run_id"]) == expected_mode
        assert record["run_id"] == run_id

    invalid_run_ids = [
        "run-abc-push-py3.10-warning",
        "run-1234-push-main-py3.10",
        "run-1234-schedule-py3.10-warning-extra",
    ]
    for run_id in invalid_run_ids:
        monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", run_id)
        with pytest.raises(ValueError, match="PASS_39_LATENCY_METRICS_RUN_ID with 'run-' prefix"):
            _maybe_write_latency_metrics(
                str(output),
                winner_latency_ms=[12.0],
                failure_count=0,
                worker_count=2,
                total_messages=1,
                thresholds={
                    "max_p95_ms": 2500.0,
                    "max_p99_ms": 3500.0,
                    "max_failure_ratio": 0.85,
                },
                p95_ms=12.0,
                p99_ms=12.0,
                max_ms=12.0,
                failure_ratio=0.0,
                warnings=[],
            )
    rejection_entries = [
        json.loads(line)
        for line in rejection_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rejection_entries) == len(invalid_run_ids)
    for entry, expected_run_id in zip(rejection_entries, invalid_run_ids, strict=True):
        assert entry["run_id"] == expected_run_id
        assert entry["kind"] == "pass39-latency-metrics-run-id-rejection"
        assert entry["reason"] == "PASS_39_LATENCY_METRICS_RUN_ID with 'run-' prefix must follow CI pattern"
        assert entry["expected_pattern"].startswith("run-<run-id>-")
        assert "warning" in entry["expected_pattern"]
        assert "main" in entry["expected_pattern"]
        assert "schedule" in entry["expected_pattern"]
        assert entry["expected_mode"] == "ci"

    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "manual-2026-06-09-local-run")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[13.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=13.0,
        p99_ms=13.0,
        max_ms=13.0,
        failure_ratio=0.0,
        warnings=[],
    )
    record = json.loads(output.read_text(encoding="utf-8").splitlines()[-1])
    assert _classify_latency_run_id(record["run_id"]) == "manual"
    assert record["run_id"] == "manual-2026-06-09-local-run"


_ISO8601_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z")
_CI_WARNING_RUN_ID_RE = re.compile(r"^run-(?P<run_id>\d+)-(?P<event>[a-z0-9_]+)-py(?P<py>\d+\.\d+)-warning$")
_CI_MAIN_RUN_ID_RE = re.compile(
    r"^run-(?P<run_id>\d+)-(?P<event>[a-z0-9_]+)-main-py(?P<py>\d+\.\d+)-fail-(?P<sha>[0-9a-f]{7,40})$"
)
_CI_SCHEDULE_RUN_ID_RE = re.compile(
    r"^run-(?P<run_id>\d+)-(?P<event>[a-z0-9_]+)(?:-schedule)?-py(?P<py>\d+\.\d+)-fail$"
)


def _classify_latency_run_id(run_id: str) -> str:
    if _CI_WARNING_RUN_ID_RE.fullmatch(run_id):
        return "warning"
    if _CI_MAIN_RUN_ID_RE.fullmatch(run_id):
        return "main"
    if _CI_SCHEDULE_RUN_ID_RE.fullmatch(run_id):
        return "schedule"
    if run_id.startswith("run-"):
        return "invalid"
    return "manual"


def _record_run_id_rejection(
    run_id: str,
    *,
    reason: str,
    expected_pattern: str | None = None,
) -> None:
    log_path = os.getenv("PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH", "")
    if log_path.strip() == "":
        return
    final_expected_pattern = (
        expected_pattern
        if expected_pattern is not None
        else _expected_ci_run_id_patterns("<run-id>")
    )
    payload = {
        "schema_version": "pass39-latency-run-id-rejection-v1",
        "kind": "pass39-latency-metrics-run-id-rejection",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "reason": reason,
        "expected_pattern": final_expected_pattern,
        "expected_mode": _expected_mode_for_run_id(run_id),
        "rejection_log_path": str(log_path),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_event_name": os.getenv("GITHUB_EVENT_NAME"),
    }
    try:
        _append_jsonl_record(log_path, payload)
    except OSError as exc:
        warnings.warn(
            _Pass39LatencyRunIdRejectionLogWarning(
                reason="PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH write failed",
                log_path=str(log_path),
                error=str(exc),
            ),
            stacklevel=2,
        )
        return


def _assert_latency_metric_run_id_is_expected(run_id: str) -> None:
    mode = _classify_latency_run_id(run_id)
    if mode == "invalid":
        reason = (
            "PASS_39_LATENCY_METRICS_RUN_ID with 'run-' prefix must follow CI pattern"
        )
        _record_run_id_rejection(run_id, reason=reason)
        raise ValueError(reason)
    if mode == "manual" and not (
        run_id.startswith("RUN-") or re.match(r"^manual-\d", run_id) is not None
    ):
        reason = "PASS_39_LATENCY_METRICS_RUN_ID must be 'manual-*' when not using run-* patterns"
        _record_run_id_rejection(
            run_id,
            reason=reason,
            expected_pattern="run-id must be no-whitespace and follow run-* CI patterns or manual-*",
        )
        raise ValueError(reason)


def _build_latency_metric_run_id(*, default_timestamp: str) -> str:
    raw_run_id = os.getenv("PASS_39_LATENCY_METRICS_RUN_ID", "")
    run_id = raw_run_id.strip()
    if run_id == "":
        return default_timestamp
    if " " in run_id or "\n" in run_id or "\r" in run_id:
        reason = "PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace"
        _record_run_id_rejection(
            run_id,
            reason=reason,
            expected_pattern="run-id must be no-whitespace and follow run-* CI patterns or manual-*",
        )
        raise ValueError(reason)
    _assert_latency_metric_run_id_is_expected(run_id)
    return run_id


def test_latency_metric_policy_summary_allows_warning_mode(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "policy.jsonl"
    monkeypatch.setenv("PASS_39_LATENCY_METRICS_RUN_ID", "RUN-2026-06-09-pass39-policy")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[5.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=12.0,
        p99_ms=12.0,
        max_ms=12.0,
        failure_ratio=0.0,
        warnings=["sample warning for policy test"],
    )
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[4.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=4.0,
        p99_ms=4.0,
        max_ms=4.0,
        failure_ratio=0.0,
        warnings=[],
    )

    records = _load_latency_metric_records(str(output))
    summary = _summarize_latency_metric_records(records)
    assert summary["records"] == 2
    assert summary["warning_records"] == 1
    assert summary["max_warning_count"] == 1
    assert summary["failed_records"] == ["RUN-2026-06-09-pass39-policy"]
    assert summary["all_ok"] is False


def test_latency_policy_allows_warning_mode_by_default(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "policy-default.jsonl"
    monkeypatch.setenv("PASS_39_LATENCY_POLICY", "warning-only")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[12.0],
        failure_count=0,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=10.0,
        p99_ms=10.0,
        max_ms=10.0,
        failure_ratio=0.0,
        warnings=["warn-1"],
    )
    records = _load_latency_metric_records(str(output))
    passed, report = _evaluate_latency_policy(records, _policy_mode_from_env(), max_warning_count=0)
    assert passed is True
    assert report["policy_mode"] == "warning-only"
    assert report["reason"] == []


def test_latency_policy_fail_mode_blocks_warning_records(tmp_path, monkeypatch):
    output = tmp_path / "artifacts" / "policy-fail.jsonl"
    monkeypatch.setenv("PASS_39_LATENCY_POLICY", "fail-on-warning")
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[12.0],
        failure_count=1,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=15.0,
        p99_ms=15.0,
        max_ms=15.0,
        failure_ratio=0.5,
        warnings=["warn-2"],
    )
    records = _load_latency_metric_records(str(output))
    passed, report = _evaluate_latency_policy(records, _policy_mode_from_env(), max_warning_count=0)
    assert passed is False
    assert report["policy_mode"] == "fail-on-warning"
    assert report["reason"]


def test_latency_policy_max_warning_count_guard(tmp_path):
    output = tmp_path / "artifacts" / "policy-max.jsonl"
    _maybe_write_latency_metrics(
        str(output),
        winner_latency_ms=[12.0],
        failure_count=1,
        worker_count=2,
        total_messages=1,
        thresholds={
            "max_p95_ms": 2500.0,
            "max_p99_ms": 3500.0,
            "max_failure_ratio": 0.85,
        },
        p95_ms=15.0,
        p99_ms=15.0,
        max_ms=15.0,
        failure_ratio=0.5,
        warnings=["warn-a", "warn-b", "warn-c"],
    )
    records = _load_latency_metric_records(str(output))
    passed, report = _evaluate_latency_policy(records, "fail-on-warning", max_warning_count=2)
    assert passed is False
    assert report["reason"]


def _setup_paths(module, tmp_path: Path):
    inbox = tmp_path / "agents" / "messages" / "inbox"
    runtime = tmp_path / "agents" / "runtime"
    inbox.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    module.MESSAGES_INBOX = inbox
    module.RUNTIME_DIR = runtime
    module.CLAIMS_DIR = runtime / "claims"


def _write_message(module, inbox: Path, message_id: str, *, status="open") -> Path:
    path = inbox / f"{message_id}.md"
    path.write_text(
        "\n".join([
            "---",
            f"id: {message_id}",
            "from: orchestrator",
            "to: qa",
            f"status: {status}",
            "intent: queue race",
            "ts: 2026-06-08T11:11:11+09:00",
            "---",
            "process this message",
            "",
        ]),
        encoding="utf-8",
    )
    return path


def test_concurrent_claim_has_exactly_one_winner(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    inbox = mq.MESSAGES_INBOX

    message = _write_message(mq, inbox, "MSG-20260608-111111-test")

    start = threading.Barrier(12)

    def attempt() -> bool:
        # Make claim attempts overlap.
        start.wait()
        txt = message.read_text(encoding="utf-8")
        meta, body = mq.parse_frontmatter(txt)
        return mq.claim_message(message, meta, body, role="qa")

    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(lambda _: attempt(), range(12)))

    assert results.count(True) == 1, results
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"
    assert (mq.CLAIMS_DIR / f"{message.stem}.claim").exists()


def test_concurrent_claim_mp_has_exactly_one_winner(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666666-test")

    start_event = Event()
    result_queue: Queue = Queue()
    procs = [
        Process(
            target=_multiprocess_claim_worker,
            args=(
                str(message),
                str(MESSAGE_QUEUE),
                str(mq.MESSAGES_INBOX),
                str(mq.RUNTIME_DIR),
                "qa",
                start_event,
                result_queue,
            ),
        )
        for _ in range(8)
    ]

    for p in procs:
        p.start()

    start_event.set()

    for p in procs:
        p.join(timeout=5)

    results = []
    for _ in procs:
        try:
            results.append(result_queue.get(timeout=5))
        except queue.Empty:
            results.append(False)

    assert len(results) == len(procs), results
    assert results.count(True) == 1, results

    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"
    assert (mq.CLAIMS_DIR / f"{message.stem}.claim").exists()


def test_mark_answered_is_owner_only(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-222222-test")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    assert mq.claim_message(message, meta, body, role="qa")

    assert mq.mark_answered(message, role="owner") is False
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"

    assert mq.mark_answered(message, role="qa") is True
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "answered"


def test_mark_answered_blocks_mismatched_worker_identity(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-777777-test")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    assert mq.claim_message(message, meta, body, role="qa")

    claim = mq._read_claim(mq._claim_path("MSG-20260608-777777-test"))
    assert isinstance(claim, dict)

    bad_worker = {"pid": int(claim.get("pid", 0) or 0) + 1234, "hostname": claim.get("hostname", "host")}
    assert mq.mark_answered(message, role="qa", worker_identity=bad_worker) is False
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"

    good_worker = {"pid": claim.get("pid"), "hostname": claim.get("hostname")}
    assert mq.mark_answered(message, role="qa", worker_identity=good_worker) is True
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "answered"


def test_has_active_claim_rejects_stale_frontmatter_claim(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-101010-stale-meta")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    assert mq.claim_message(message, meta, body, role="qa")

    meta["claim"] = {
        "role": "qa",
        "pid": 1234,
        "hostname": "host",
        "claimed_at": 1.0,
        "expires_at": 2.0,
    }
    message.write_text(mq.serialize_frontmatter(meta, body), encoding="utf-8")
    mq._release_claim("MSG-20260608-101010-stale-meta")

    assert mq.has_active_claim(message, role="qa") is False
    assert mq.mark_answered(message, role="qa") is False


def test_has_active_claim_reflects_owner(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-999999-owner")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    assert mq.claim_message(message, meta, body, role="qa")

    assert mq.has_active_claim(message, role="qa") is True
    assert mq.has_active_claim(message, role="owner") is False

    claim = mq._read_claim(mq._claim_path("MSG-20260608-999999-owner"))
    assert claim is not None
    fake = {"pid": claim["pid"], "hostname": claim["hostname"]}
    assert mq.has_active_claim(message, role="qa", worker_identity=fake) is True
    bad = {"pid": int(claim["pid"]) + 7, "hostname": claim["hostname"]}
    assert mq.has_active_claim(message, role="qa", worker_identity=bad) is False


def test_claim_token_enforces_owner_consistency(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666668-token")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    assert mq.claim_message(message, meta, body, role="qa")

    claim = mq._read_claim(mq._claim_path("MSG-20260608-666668-token"))
    assert isinstance(claim, dict)
    token = claim.get("token")
    assert token

    wrong = {"token": f"bad-{token}"}
    assert mq.mark_answered(message, role="qa", worker_identity=wrong) is False

    same = {"token": str(token)}
    assert mq.mark_answered(message, role="qa", worker_identity=same) is True

    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "answered"


def test_mark_answered_accepts_existing_reply_as_completed(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-999998-existing-reply", status="claimed")

    msg_id = "MSG-20260608-999998-existing-reply"
    reply = mq.MESSAGES_INBOX / f"{msg_id}-reply.md"
    reply.write_text(
        "\n".join([
            "---",
            f"id: {msg_id}-reply",
            "from: qa",
            "to: orchestrator",
            "type: reply",
            "status: complete",
            f"in_reply_to: {msg_id}",
            "---",
            "already answered",
            "",
        ]),
        encoding="utf-8",
    )

    # Existing reply should make status transition idempotent and not fail ownership.
    assert mq.mark_answered(message, role="qa") is True
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "answered"
def test_recover_stale_claim_restores_open_when_no_reply(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-333333-test", status="claimed")
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    message_id = "MSG-20260608-333333-test"

    claim_path = mq._claim_path(message_id)
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 12345,
        "hostname": "unit-test",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": str(message_id),
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    assert mq.recover_stale_claim(message) is True
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "open"


def test_recover_stale_claim_rejects_path_mismatch(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-888888-test", status="claimed")

    message_id = "MSG-20260608-888888-test"
    claim_path = mq._claim_path(message_id)
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 12345,
        "hostname": "unit-test",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": "/different/working/tree/message.md",
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    assert mq.recover_stale_claim(message) is False
    assert not claim_path.exists()


def test_recover_stale_claim_obeys_skewed_clock_override(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(
        mq,
        mq.MESSAGES_INBOX,
        "MSG-20260608-131313-clock",
        status="claimed",
    )
    message_id = "MSG-20260608-131313-clock"
    claim_path = mq._claim_path(message_id)
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 1111,
        "hostname": "unit-test",
        "claimed_at": 10.0,
        "expires_at": 20.0,
        "path": str(message_id),
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    # A worker with a slightly behind clock must keep stale claim.
    assert mq.recover_stale_claim(message, now=10.0) is False
    assert claim_path.exists()

    # A worker with a forward clock should treat the same lease as stale and recover.
    assert mq.recover_stale_claim(message, now=21.0) is True
    assert not claim_path.exists()


def test_parallel_recover_and_answer_multiple_messages_with_skewed_replay_delay(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    inbox = mq.MESSAGES_INBOX

    messages = [
        _write_message(
            mq,
            inbox,
            f"MSG-20260609-{idx:03d}-multi-msg",
            status="claimed",
        )
        for idx in range(8)
    ]
    for idx, message in enumerate(messages):
        message_id = message.stem
        claim_path = mq._claim_path(message_id)
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(
            json.dumps(
                {
                    "message_id": message_id,
                    "role": "qa",
                    "pid": 1000 + idx,
                    "hostname": "unit-test",
                    "claimed_at": 1.0,
                    "expires_at": 2.0,
                    "path": message_id,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    start_event = Event()
    result_queue: Queue = Queue()
    delay_plan = [0.0, 0.0, 0.05, 0.05, 0.1, 0.1]
    workers = []
    for idx, message in enumerate(messages):
        path = str(message)
        recovery_delay = delay_plan[idx % len(delay_plan)]
        workers.append(
            Process(
                target=_multiprocess_stale_recover_and_answer_worker,
                args=(
                    path,
                    str(MESSAGE_QUEUE),
                    str(mq.MESSAGES_INBOX),
                    str(mq.RUNTIME_DIR),
                    "qa",
                    100.0,
                    start_event,
                    result_queue,
                    0.01 * idx,
                    recovery_delay,
                ),
            ),
        )
        workers.append(
            Process(
                target=_multiprocess_stale_recover_and_answer_worker,
                args=(
                    path,
                    str(MESSAGE_QUEUE),
                    str(mq.MESSAGES_INBOX),
                    str(mq.RUNTIME_DIR),
                    "qa",
                    1.0,
                    start_event,
                    result_queue,
                    0.01 * idx + 0.005,
                    0.0,
                ),
            ),
        )

    for worker in workers:
        worker.start()
    start_event.set()

    for worker in workers:
        worker.join(timeout=10)

    results = []
    for _ in workers:
        try:
            results.append(result_queue.get(timeout=5))
        except queue.Empty:
            results.append((None, False))

    assert len(results) == len(workers), results
    done_map: dict[str, int] = {}
    for path, ok in results:
        if ok:
            done_map[path] = done_map.get(path, 0) + 1

    assert len(done_map) == len(messages)
    assert all(count == 1 for count in done_map.values())

    for message in messages:
        meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
        assert meta.get("status") == "answered"

    reply_files = [
        file
        for file in inbox.iterdir()
        if file.suffix == ".md" and file.name not in [message.name for message in messages]
    ]
    assert len(reply_files) == len(messages)
    for message in messages:
        hit_count = 0
        for file in reply_files:
            reply_meta, _ = mq.parse_frontmatter(file.read_text(encoding="utf-8"))
            if reply_meta.get("in_reply_to") == message.stem:
                hit_count += 1
        assert hit_count == 1


def test_parallel_recover_and_answer_latency_distribution_and_starvation_guard(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    inbox = mq.MESSAGES_INBOX

    messages = [
        _write_message(
            mq,
            inbox,
            f"MSG-20260609-LAT-{idx:03d}",
            status="claimed",
        )
        for idx in range(10)
    ]
    for idx, message in enumerate(messages):
        message_id = message.stem
        claim_path = mq._claim_path(message_id)
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(
            json.dumps(
                {
                    "message_id": message_id,
                    "role": "qa",
                    "pid": 8000 + idx,
                    "hostname": "unit-test",
                    "claimed_at": 1.0,
                    "expires_at": 2.0,
                    "path": message_id,
                },
            ),
            encoding="utf-8",
        )

    start_event = Event()
    result_queue: Queue = Queue()
    workers = []
    pre_plan = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]
    post_plan = [0.0, 0.01, 0.02, 0.0, 0.01, 0.02]
    for idx, message in enumerate(messages):
        path = str(message)
        pre_delay = pre_plan[idx % len(pre_plan)]
        post_delay = post_plan[idx % len(post_plan)]
        workers.append(
            Process(
                target=_multiprocess_timed_stale_recover_and_answer_worker,
                args=(
                    path,
                    str(MESSAGE_QUEUE),
                    str(mq.MESSAGES_INBOX),
                    str(mq.RUNTIME_DIR),
                    "qa",
                    100.0,
                    start_event,
                    result_queue,
                    pre_delay,
                    post_delay,
                ),
            ),
        )
        workers.append(
            Process(
                target=_multiprocess_timed_stale_recover_and_answer_worker,
                args=(
                    path,
                    str(MESSAGE_QUEUE),
                    str(mq.MESSAGES_INBOX),
                    str(mq.RUNTIME_DIR),
                    "qa",
                    1.0,
                    start_event,
                    result_queue,
                    pre_delay + 0.05,
                    0.0,
                ),
            ),
        )

    for worker in workers:
        worker.start()
    start_event.set()

    for worker in workers:
        worker.join(timeout=12)

    results = []
    for _ in workers:
        try:
            results.append(result_queue.get(timeout=5))
        except queue.Empty:
            results.append((None, False, None))

    assert len(results) == len(workers), results
    by_message: dict[str, list[float]] = {}
    failure_count = 0
    for item in results:
        path, ok, elapsed_ms = item
        if not ok:
            failure_count += 1
            continue
        by_message.setdefault(path, []).append(elapsed_ms if elapsed_ms is not None else 0.0)

    assert len(by_message) == len(messages), by_message
    success_counts = [len(v) for v in by_message.values()]
    assert all(count >= 1 for count in success_counts)

    winner_latency_ms: list[float] = [min(v) for v in by_message.values() if v]
    winner_latency_ms.sort()
    assert winner_latency_ms
    p95_ms = _percentile_ms(winner_latency_ms, 0.95)
    p99_ms = _percentile_ms(winner_latency_ms, 0.99)
    max_ms = max(winner_latency_ms)
    failure_ratio = failure_count / len(workers)

    warnings: list[str] = []
    # PASS-38 SLO targets
    max_p95_ms = _env_float("PASS_39_MAX_P95_MS", 2500.0)
    max_p99_ms = _env_float("PASS_39_MAX_P99_MS", 3500.0)
    max_failure_ratio = _env_float("PASS_39_MAX_FAILURE_RATIO", 0.85)
    if p95_ms > max_p95_ms:
        warnings.append(f"p95_ms={p95_ms:.2f}ms exceeds {max_p95_ms:.2f}ms")
    if p99_ms > max_p99_ms:
        warnings.append(f"p99_ms={p99_ms:.2f}ms exceeds {max_p99_ms:.2f}ms")
    if failure_ratio > max_failure_ratio:
        warnings.append(
            f"failure_ratio={failure_ratio:.2f} exceeds {max_failure_ratio:.2f}"
        )
    _maybe_write_latency_metrics(
        os.getenv("PASS_39_LATENCY_METRICS_PATH", ""),
        winner_latency_ms=winner_latency_ms,
        failure_count=failure_count,
        worker_count=len(workers),
        total_messages=len(messages),
        thresholds={
            "max_p95_ms": max_p95_ms,
            "max_p99_ms": max_p99_ms,
            "max_failure_ratio": max_failure_ratio,
        },
        p95_ms=p95_ms,
        p99_ms=p99_ms,
        max_ms=max_ms,
        failure_ratio=failure_ratio,
        warnings=warnings,
    )
    if warnings:
        print(
            "PASS-38 latency alerts: "
            f"p95={p95_ms:.2f}ms, p99={p99_ms:.2f}ms, max={max_ms:.2f}ms, "
            f"failure_ratio={failure_ratio:.2f}. "
            f"{'; '.join(warnings)}"
        )

    policy_records = _load_latency_metric_records(os.getenv("PASS_39_LATENCY_METRICS_PATH", ""))
    policy_mode = _policy_mode_from_env()
    max_policy_warning_count = _env_int("PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT", None)
    policy_passed, policy_report = _evaluate_latency_policy(
        policy_records,
        policy_mode,
        max_warning_count=max_policy_warning_count,
    )
    if not policy_passed:
        print(
            "PASS-42 latency policy check failed: "
            f"mode={policy_report['policy_mode']} "
            f"reasons={policy_report['reason']}"
        )
    assert policy_passed, f"PASS-42 latency policy blocked: {policy_report['reason']}"

    answered_messages = []
    for message in messages:
        meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
        if meta.get("status") == "answered":
            answered_messages.append(message.name)
    assert len(answered_messages) == len(messages)
    assert failure_count >= len(messages)

    reply_files = [
        file
        for file in inbox.iterdir()
        if file.suffix == ".md" and file.name not in [message.name for message in messages]
    ]
    assert len(reply_files) == len(messages)
    for message in messages:
        replies = 0
        for file in reply_files:
            reply_meta, _ = mq.parse_frontmatter(file.read_text(encoding="utf-8"))
            if reply_meta.get("in_reply_to") == message.stem:
                replies += 1
        assert replies == 1


def test_concurrent_stale_recover_and_claim_has_single_winner(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666667-recover", status="claimed")

    message_id = "MSG-20260608-666667-recover"
    claim_path = mq._claim_path(message_id)
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 1111,
        "hostname": "unit-test",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": message_id,
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    start_event = Event()
    result_queue: Queue = Queue()
    procs = [
        Process(
            target=_multiprocess_recover_and_claim_worker,
            args=(
                str(message),
                str(MESSAGE_QUEUE),
                str(mq.MESSAGES_INBOX),
                str(mq.RUNTIME_DIR),
                "qa",
                start_event,
                result_queue,
            ),
        )
        for _ in range(8)
    ]

    for p in procs:
        p.start()
    start_event.set()
    for p in procs:
        p.join(timeout=5)

    results = []
    for _ in procs:
        try:
            results.append(result_queue.get(timeout=5))
        except queue.Empty:
            results.append(False)

    assert len(results) == len(procs), results
    assert results.count(True) == 1, results
    assert message.read_text(encoding="utf-8").startswith("---")
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"
    assert claim_path.exists()


def test_concurrent_recover_and_claim_with_clock_skew_has_single_winner(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-141414-skew", status="claimed")

    message_id = "MSG-20260608-141414-skew"
    claim_path = mq._claim_path(message_id)
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 2222,
        "hostname": "unit-test",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": message_id,
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    start_event = Event()
    result_queue: Queue = Queue()
    procs = [
        Process(
            target=_multiprocess_recover_and_claim_worker_with_clock_skew,
            args=(
                str(message),
                str(MESSAGE_QUEUE),
                str(mq.MESSAGES_INBOX),
                str(mq.RUNTIME_DIR),
                "qa",
                100.0,
                start_event,
                result_queue,
                0.0,
            ),
        ),
        Process(
            target=_multiprocess_recover_and_claim_worker_with_clock_skew,
            args=(
                str(message),
                str(MESSAGE_QUEUE),
                str(mq.MESSAGES_INBOX),
                str(mq.RUNTIME_DIR),
                "qa",
                1.0,
                start_event,
                result_queue,
                0.05,
            ),
        ),
    ]

    for p in procs:
        p.start()
    start_event.set()
    for p in procs:
        p.join(timeout=5)

    results = []
    for _ in procs:
        try:
            results.append(result_queue.get(timeout=5))
        except queue.Empty:
            results.append(False)

    assert len(results) == len(procs), results
    assert results.count(True) == 1, results
    assert message.read_text(encoding="utf-8").startswith("---")
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"
    assert claim_path.exists()


def test_claim_creation_retries_after_transient_fs_error(tmp_path, monkeypatch):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666669-transient")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)
    calls = {"n": 0}
    real_open = builtins.open

    def flaky_open(file, mode="r", encoding=None, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("transient fs lock")
        return real_open(file, mode, encoding=encoding, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", flaky_open)
    assert mq.claim_message(message, meta, body, role="qa") is True
    assert calls["n"] >= 2
    assert (mq.CLAIMS_DIR / f"{message.stem}.claim").exists()


def test_claim_message_retries_frontmatter_replace_after_transient_fs_delay(tmp_path, monkeypatch):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666670-transient-delay")
    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)

    replace_calls = {"n": 0}
    delays = []
    original_replace = mq.os.replace

    def flaky_replace(src, dst):
        replace_calls["n"] += 1
        if replace_calls["n"] == 1:
            raise OSError("transient distributed fs rename")
        return original_replace(src, dst)

    def capture_delay(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(mq.os, "replace", flaky_replace)
    monkeypatch.setattr(mq.time, "sleep", capture_delay)

    assert mq.claim_message(message, meta, body, role="qa") is True
    assert replace_calls["n"] == 2
    assert delays == [mq.CLAIM_CREATE_RETRY_DELAY_SECONDS]
    assert message.read_text(encoding="utf-8").startswith("---")
    after_meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert after_meta.get("status") == "claimed"
    assert (mq.CLAIMS_DIR / f"{message.stem}.claim").exists()


def test_write_text_atomic_retries_after_transient_tmp_write_failure(tmp_path, monkeypatch):
    mq = _load_message_queue()
    target = tmp_path / "queue_atomic_retry.md"

    calls = {"tmp_open": 0}
    original_write_text = mq.Path.write_text

    def flaky_write_text(path: mq.Path, text: str, *args, **kwargs):
        name = str(path)
        if ".tmp." in name:
            calls["tmp_open"] += 1
            if calls["tmp_open"] == 1:
                raise OSError("transient tmp write failure")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(mq.Path, "write_text", flaky_write_text)
    assert mq._write_text_atomic(target, "hello", attempts=3, delay_seconds=0.0) is True
    assert calls["tmp_open"] >= 1
    assert target.read_text(encoding="utf-8") == "hello"


def test_write_text_atomic_fails_and_cleans_up_when_tmp_write_keeps_failing(tmp_path, monkeypatch):
    mq = _load_message_queue()
    target = tmp_path / "queue_atomic_fail.md"
    observed = {"tmp_open": 0}
    original_write_text = mq.Path.write_text

    def always_fail_tmp_write(path: mq.Path, text: str, *args, **kwargs):
        name = str(path)
        if ".tmp." in name:
            observed["tmp_open"] += 1
            raise OSError("persistent tmp write failure")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(mq.Path, "write_text", always_fail_tmp_write)
    assert mq._write_text_atomic(target, "hello", attempts=2, delay_seconds=0.0) is False
    assert observed["tmp_open"] >= 2
    assert not target.exists()
    assert not any(".tmp." in path.name for path in target.parent.iterdir())


def test_claim_message_releases_claim_when_frontmatter_replace_keeps_failing(tmp_path, monkeypatch):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-666671-frontmatter-fail")
    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)

    def always_fail_replace(src, dst):
        raise OSError("shared fs rename lock")

    monkeypatch.setattr(mq.os, "replace", always_fail_replace)
    monkeypatch.setattr(mq.time, "sleep", lambda _seconds: None)

    assert mq.claim_message(message, meta, body, role="qa") is False
    assert not (mq.CLAIMS_DIR / f"{message.stem}.claim").exists()
    after_meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert after_meta.get("status") == "open"


def test_claim_recovers_from_malformed_claim_file(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-121212-malformed")

    claim_path = mq._claim_path("MSG-20260608-121212-malformed")
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text("{not json", encoding="utf-8")

    text = message.read_text(encoding="utf-8")
    meta, body = mq.parse_frontmatter(text)

    assert mq.claim_message(message, meta, body, role="qa") is True
    assert claim_path.exists()
    assert mq._read_claim(claim_path)

    # claim payload should now be recoverable JSON owned by this process.
    payload = mq._read_claim(claim_path)
    assert isinstance(payload, dict)
    assert payload.get("role") == "qa"


def test_recover_stale_claim_with_reply_keeps_claim_file_gating(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-444444-test", status="claimed")
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    message_id = meta["id"]

    claim_path = mq._claim_path(str(message_id))
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    stale = {
        "message_id": message_id,
        "role": "qa",
        "pid": 12345,
        "hostname": "unit-test",
        "claimed_at": 1.0,
        "expires_at": 2.0,
        "path": str(message_id),
    }
    claim_path.write_text(json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")

    # Existing reply blocks stale reclaim.
    reply = mq.MESSAGES_INBOX / f"{message_id}-reply.md"
    reply.write_text(
        f"---\nid: {message_id}-reply\nin_reply_to: {message_id}\ntype: reply\n---\nok\n",
        encoding="utf-8",
    )

    assert mq.recover_stale_claim(message) is False
    meta, _ = mq.parse_frontmatter(message.read_text(encoding="utf-8"))
    assert meta.get("status") == "claimed"
    assert not claim_path.exists()


def test_one_reply_written_with_competing_workers(tmp_path):
    mq = _load_message_queue()
    _setup_paths(mq, tmp_path)
    message = _write_message(mq, mq.MESSAGES_INBOX, "MSG-20260608-555555-test")

    start = threading.Barrier(8)

    def run_worker() -> bool:
        start.wait()
        txt = message.read_text(encoding="utf-8")
        meta, body = mq.parse_frontmatter(txt)
        if not mq.claim_message(message, meta, body, role="qa"):
            return False
        reply = mq.MESSAGES_INBOX / f"{uuid.uuid4().hex}.md"
        reply.write_text(
            "\n".join([
                "---",
                "id: " + reply.stem,
                "from: qa",
                "to: orchestrator",
                "type: reply",
                "status: complete",
                f"in_reply_to: {meta['id']}",
                "---",
                "ok",
                "",
            ]),
            encoding="utf-8",
        )
        mq.mark_answered(message, role="qa")
        return True

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda _: run_worker(), range(8)))

    assert results.count(True) == 1
    replies = [p for p in mq.MESSAGES_INBOX.iterdir() if p != message]
    assert len(replies) == 1
    _, body = mq.parse_frontmatter(replies[0].read_text(encoding="utf-8"))
    assert "ok" in body
