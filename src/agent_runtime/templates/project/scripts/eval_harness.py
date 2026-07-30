#!/usr/bin/env python3
"""eval_harness — agentic 측정 substrate (TASK-238, 15패턴 ①).

라우팅(239)·협업(240)·생성트리오(242)가 **baseline 대비 개선을 증명하는 분모**.
architect subagent(collab-2026-06-05.jsonl): 측정은 peer 아닌 선행 의존 — 없으면 피드백
루프가 merge 시 unfalsifiable(soft 로그 재발).

구성:
  - record_outcome  : per-task outcome/usage 로그(eval_log.jsonl, gitignore = 런타임 데이터).
  - judge_outcome   : **객관 신호**(finish_reason·outcome)로 분류 — LLM-judge 아님(순환 회피).
  - report          : grade/model 별 usage·escalation 집계 + 검증된 token/billed-cost delta.
  - golden set      : 판정 회귀 가드(committed fixture, agents/lead_engineer/eval/golden.jsonl).

"맞는 모델" = escalation 신호 없이 끝낸 가장 싼 tier(별도 judge 모델 불요).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
EVAL_LOG = ROOT / "eval_log.jsonl"                       # gitignore (런타임)
GOLDEN = ROOT / "agents" / "lead_engineer" / "eval" / "golden.jsonl"  # committed fixture

import model_routing  # noqa: E402

# 객관 escalation 신호(model 이 약했거나 task 가 컸다 — under-route).
# 'length' 는 ambiguous(성공한 긴 출력일 수 있음) → outcome 도 나쁠 때만 escalate(reviewer #1).
ESCALATION_FINISH = {"error", "cap", "cap-hit", "max_tokens"}
ESCALATION_OUTCOME = {"rejected", "needs-changes", "gate-error", "recurrence", "reopen"}
NEUTRAL_OUTCOME = {"ok", "completed", ""}
MODEL_TIER = {"haiku": 1, "sonnet": 2, "opus": 3}       # 싼→비싼 (TASK-239 over-route 판정용)
SUCCESSFUL_EXECUTION_FINISH = {
    "completed",
    "end_turn",
    "stop",
    "stop_sequence",
    "success",
}
NO_PROVIDER_SETTLEMENT_TRANSITIONS = {
    ("auto_dispatch", "claim_preflight"),
    ("auto_dispatch", "session_budget_preflight"),
}
PROVIDER_CALL_START_TRANSITIONS = {
    ("agent_worker", "agent_worker_provider_run"): frozenset(
        {
            "provider_completion",
            "provider_error",
            "provider_exception",
            "provider_unsupported",
        }
    ),
    ("auto_dispatch", "auto_dispatch_provider_run"): frozenset(
        {"provider_completion", "provider_error"}
    ),
    ("codex_subagent_bridge", "native_codex_authorize"): frozenset(
        {"native_codex_reply"}
    ),
    ("codex_subagent_council", "native_codex_authorize"): frozenset(
        {"native_codex_council_reply"}
    ),
    ("verify_sdk_backend", "verify_sdk_provider_run"): frozenset(
        {"verify_sdk_backend"}
    ),
}
PROVIDER_RESULT_STATUSES = {"completed", "error"}

EXECUTION_RECEIPT_SCHEMA = "agent-runtime-execution-receipt/v1"
BUDGET_RESERVATION_SCHEMA = "agent-runtime-budget-reservation/v1"
NO_PROVIDER_SETTLEMENT_SCHEMA = (
    "agent-runtime-no-provider-settlement/v1"
)
PROVIDER_CALL_START_SCHEMA = "agent-runtime-provider-call-start/v1"
RECEIPT_LOCK_TIMEOUT_SECONDS = 5.0
ACTIVE_CLAIM_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------- logger ----------


class ReceiptConflictError(ValueError):
    """A dispatch already has an immutable receipt."""


class ReceiptIntegrityError(RuntimeError):
    """The append-only receipt ledger cannot be trusted."""


@contextmanager
def _exclusive_log_lock(path: Path):
    """Cross-platform exclusive lock for one append-only JSONL ledger."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    deadline = time.monotonic() + RECEIPT_LOCK_TIMEOUT_SECONDS
    fd: int | None = None
    while fd is None:
        try:
            fd = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ReceiptIntegrityError(
                    f"receipt ledger lock timed out: {lock_path}"
                )
            time.sleep(0.01)
    try:
        os.write(fd, str(os.getpid()).encode("ascii", errors="strict"))
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _reservation_fingerprint(reservation: dict) -> str:
    """Bind a settlement to the complete immutable reservation record."""
    return hashlib.sha256(
        json.dumps(
            reservation,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _provider_call_start_id(
    reservation_id: str,
    source: str,
    provider: str,
    execution_surface: str,
) -> str:
    return "provider-call-start-" + hashlib.sha256(
        (
            f"{reservation_id}:{source}:"
            f"{provider}:{execution_surface}"
        ).encode("utf-8")
    ).hexdigest()[:24]


def _validate_ledger_records(records: list[dict], path: Path) -> None:
    receipt_ids: dict[str, int] = {}
    reservation_ids: dict[str, int] = {}
    settlement_ids: dict[str, int] = {}
    call_start_ids: dict[str, int] = {}
    dispatch_kinds: dict[str, dict[str, int]] = {}
    reservations: dict[str, dict] = {}
    receipts: dict[str, dict] = {}
    settlements: dict[str, dict] = {}
    call_starts: dict[str, dict] = {}

    for index, item in enumerate(records, start=1):
        schema = str(item.get("schema") or "")
        dispatch_id = str(item.get("dispatch_id") or "").strip()
        if schema in {
            EXECUTION_RECEIPT_SCHEMA,
            BUDGET_RESERVATION_SCHEMA,
            NO_PROVIDER_SETTLEMENT_SCHEMA,
            PROVIDER_CALL_START_SCHEMA,
        }:
            if item.get("immutable") is not True:
                raise ReceiptIntegrityError(
                    f"ledger line {index} is not immutable: {path}"
                )
            if not dispatch_id or not str(item.get("task_id") or "").strip():
                raise ReceiptIntegrityError(
                    f"ledger line {index} lacks dispatch_id/task_id: {path}"
                )

        if schema == EXECUTION_RECEIPT_SCHEMA:
            receipt_id = str(item.get("receipt_id") or "").strip()
            if not receipt_id:
                raise ReceiptIntegrityError(
                    f"execution receipt line {index} lacks receipt_id: {path}"
                )
            if receipt_id in receipt_ids:
                raise ReceiptIntegrityError(
                    f"duplicate receipt_id={receipt_id} at lines "
                    f"{receipt_ids[receipt_id]} and {index}: {path}"
                )
            receipt_ids[receipt_id] = index
            receipts[dispatch_id] = item
            kind = "receipt"
        elif schema == BUDGET_RESERVATION_SCHEMA:
            reservation_id = str(item.get("reservation_id") or "").strip()
            if not reservation_id:
                raise ReceiptIntegrityError(
                    f"budget reservation line {index} lacks reservation_id: {path}"
                )
            if reservation_id in reservation_ids:
                raise ReceiptIntegrityError(
                    f"duplicate reservation_id={reservation_id} at lines "
                    f"{reservation_ids[reservation_id]} and {index}: {path}"
                )
            reservation_ids[reservation_id] = index
            try:
                reserved_tokens = int(item.get("reserved_tokens"))
            except (TypeError, ValueError) as exc:
                raise ReceiptIntegrityError(
                    f"reservation line {index} has invalid reserved_tokens: {path}"
                ) from exc
            if reserved_tokens < 0:
                raise ReceiptIntegrityError(
                    f"reservation line {index} has negative reserved_tokens: {path}"
                )
            reservations[dispatch_id] = item
            kind = "reservation"
        elif schema == NO_PROVIDER_SETTLEMENT_SCHEMA:
            settlement_id = str(item.get("settlement_id") or "").strip()
            if not settlement_id:
                raise ReceiptIntegrityError(
                    f"no-provider settlement line {index} lacks "
                    f"settlement_id: {path}"
                )
            if settlement_id in settlement_ids:
                raise ReceiptIntegrityError(
                    f"duplicate settlement_id={settlement_id} at lines "
                    f"{settlement_ids[settlement_id]} and {index}: {path}"
                )
            settlement_ids[settlement_id] = index
            settlements[dispatch_id] = item
            kind = "no_provider_settlement"
        elif schema == PROVIDER_CALL_START_SCHEMA:
            call_start_id = str(item.get("call_start_id") or "").strip()
            if not call_start_id:
                raise ReceiptIntegrityError(
                    f"provider call-start line {index} lacks "
                    f"call_start_id: {path}"
                )
            if call_start_id in call_start_ids:
                raise ReceiptIntegrityError(
                    f"duplicate call_start_id={call_start_id} at lines "
                    f"{call_start_ids[call_start_id]} and {index}: {path}"
                )
            call_start_ids[call_start_id] = index
            call_starts[dispatch_id] = item
            kind = "provider_call_start"
        else:
            kind = "legacy"

        if dispatch_id:
            kinds = dispatch_kinds.setdefault(dispatch_id, {})
            if kind in kinds:
                raise ReceiptIntegrityError(
                    f"duplicate dispatch_id={dispatch_id} {kind} at lines "
                    f"{kinds[kind]} and {index}: {path}"
                )
            if kind == "legacy" and kinds:
                raise ReceiptIntegrityError(
                    f"duplicate dispatch_id={dispatch_id} at line {index}: {path}"
                )
            if kind != "legacy" and "legacy" in kinds:
                raise ReceiptIntegrityError(
                    f"duplicate dispatch_id={dispatch_id} at line {index}: {path}"
                )
            kinds[kind] = index

    for dispatch_id in sorted(set(reservations) & set(receipts)):
        reservation = reservations[dispatch_id]
        receipt = receipts[dispatch_id]
        if str(reservation.get("task_id")) != str(receipt.get("task_id")):
            raise ReceiptIntegrityError(
                f"reservation/receipt task mismatch for dispatch_id={dispatch_id}: "
                f"{path}"
            )
        if str(reservation.get("claim_id") or "") != str(
            receipt.get("claim_id") or ""
        ):
            raise ReceiptIntegrityError(
                f"reservation/receipt claim mismatch for dispatch_id={dispatch_id}: "
                f"{path}"
            )

    for dispatch_id, call_start in call_starts.items():
        reservation = reservations.get(dispatch_id)
        receipt = receipts.get(dispatch_id)
        settlement = settlements.get(dispatch_id)
        if reservation is None:
            raise ReceiptIntegrityError(
                "provider call-start requires a matching reservation for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if settlement is not None:
            raise ReceiptIntegrityError(
                "provider call-start conflicts with no-provider settlement "
                f"for dispatch_id={dispatch_id}: {path}"
            )
        if str(call_start.get("reservation_id") or "") != str(
            reservation.get("reservation_id") or ""
        ):
            raise ReceiptIntegrityError(
                "provider call-start reservation mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        for field in ("task_id", "claim_id"):
            if str(call_start.get(field) or "") != str(
                reservation.get(field) or ""
            ):
                raise ReceiptIntegrityError(
                    f"provider call-start {field} mismatch for "
                    f"dispatch_id={dispatch_id}: {path}"
                )
        reservation_source = str(
            call_start.get("reservation_source") or ""
        ).strip()
        call_source = str(call_start.get("source") or "").strip()
        if reservation_source != str(
            reservation.get("source") or ""
        ).strip():
            raise ReceiptIntegrityError(
                "provider call-start reservation source mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        allowed_receipt_sources = PROVIDER_CALL_START_TRANSITIONS.get(
            (reservation_source, call_source)
        )
        if allowed_receipt_sources is None:
            raise ReceiptIntegrityError(
                "invalid provider call-start transition "
                f"{reservation_source}->{call_source} for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if str(call_start.get("status") or "") != "provider_call_started":
            raise ReceiptIntegrityError(
                "provider call-start status mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        provider = str(call_start.get("provider") or "").strip()
        execution_surface = str(
            call_start.get("execution_surface") or ""
        ).strip()
        if not provider or not execution_surface:
            raise ReceiptIntegrityError(
                "provider call-start lacks provider/execution surface for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        expected_call_start_id = _provider_call_start_id(
            str(reservation.get("reservation_id") or ""),
            call_source,
            provider,
            execution_surface,
        )
        if str(call_start.get("call_start_id") or "") != (
            expected_call_start_id
        ):
            raise ReceiptIntegrityError(
                "provider call-start identity mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if str(call_start.get("reservation_fingerprint") or "") != (
            _reservation_fingerprint(reservation)
        ):
            raise ReceiptIntegrityError(
                "provider call-start reservation fingerprint mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if call_start.get("budget_authority_fingerprint") != dict(
            reservation.get("budget_authority") or {}
        ).get("authority_fingerprint"):
            raise ReceiptIntegrityError(
                "provider call-start budget authority mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if receipt is not None:
            if str(
                receipt.get("budget_provider_call_start_id") or ""
            ) != str(call_start.get("call_start_id") or ""):
                raise ReceiptIntegrityError(
                    "provider call-start receipt linkage mismatch for "
                    f"dispatch_id={dispatch_id}: {path}"
                )
            if str(receipt.get("provider") or "").strip() != provider:
                raise ReceiptIntegrityError(
                    "provider call-start receipt provider mismatch for "
                    f"dispatch_id={dispatch_id}: {path}"
                )
            if str(
                receipt.get("execution_surface") or ""
            ).strip() != execution_surface:
                raise ReceiptIntegrityError(
                    "provider call-start receipt execution surface mismatch "
                    f"for dispatch_id={dispatch_id}: {path}"
                )
            if str(receipt.get("source") or "").strip() not in (
                allowed_receipt_sources
            ):
                raise ReceiptIntegrityError(
                    "invalid provider call-result transition "
                    f"{call_source}->{receipt.get('source')} for "
                    f"dispatch_id={dispatch_id}: {path}"
                )

    for dispatch_id, settlement in settlements.items():
        reservation = reservations.get(dispatch_id)
        receipt = receipts.get(dispatch_id)
        if reservation is None or receipt is None:
            raise ReceiptIntegrityError(
                "no-provider settlement requires a matching reservation "
                f"and receipt for dispatch_id={dispatch_id}: {path}"
            )
        if dispatch_id in call_starts:
            raise ReceiptIntegrityError(
                "no-provider settlement conflicts with provider call-start "
                f"for dispatch_id={dispatch_id}: {path}"
            )
        if str(settlement.get("reservation_id") or "") != str(
            reservation.get("reservation_id") or ""
        ):
            raise ReceiptIntegrityError(
                "no-provider settlement reservation mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        for field in ("task_id", "claim_id"):
            if str(settlement.get(field) or "") != str(
                reservation.get(field) or ""
            ):
                raise ReceiptIntegrityError(
                    f"no-provider settlement {field} mismatch for "
                    f"dispatch_id={dispatch_id}: {path}"
                )
        reservation_source = str(
            settlement.get("reservation_source") or ""
        ).strip()
        receipt_source = str(
            settlement.get("receipt_source") or ""
        ).strip()
        if reservation_source != str(
            reservation.get("source") or ""
        ).strip():
            raise ReceiptIntegrityError(
                "no-provider settlement reservation source mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if (
            reservation_source,
            receipt_source,
        ) not in NO_PROVIDER_SETTLEMENT_TRANSITIONS:
            raise ReceiptIntegrityError(
                "invalid no-provider settlement transition "
                f"{reservation_source}->{receipt_source} for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if receipt_source != str(receipt.get("source") or "").strip():
            raise ReceiptIntegrityError(
                "no-provider settlement receipt source mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if str(settlement.get("reservation_fingerprint") or "") != (
            _reservation_fingerprint(reservation)
        ):
            raise ReceiptIntegrityError(
                "no-provider settlement reservation fingerprint mismatch "
                f"for dispatch_id={dispatch_id}: {path}"
            )
        if settlement.get("budget_authority_fingerprint") != dict(
            reservation.get("budget_authority") or {}
        ).get("authority_fingerprint"):
            raise ReceiptIntegrityError(
                "no-provider settlement budget authority mismatch for "
                f"dispatch_id={dispatch_id}: {path}"
            )
        if not _verified_pre_provider_skip(
            receipt,
            reservation,
            settlement,
        ):
            raise ReceiptIntegrityError(
                "no-provider settlement lacks a valid no-call receipt for "
                f"dispatch_id={dispatch_id}: {path}"
            )


def _strict_records(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    records: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ReceiptIntegrityError(f"receipt ledger unreadable: {path}") from exc
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReceiptIntegrityError(
                f"receipt ledger has invalid JSON at line {index}: {path}"
            ) from exc
        if not isinstance(value, dict):
            raise ReceiptIntegrityError(
                f"receipt ledger line {index} is not an object: {path}"
            )
        records.append(value)
    _validate_ledger_records(records, path)
    return records


def _append_records_locked(path: Path, records: list[dict]) -> None:
    if not records:
        return
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(
            "".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                for record in records
            )
        )
        fh.flush()
        os.fsync(fh.fileno())


def _append_record(
    path: Path,
    record: dict,
    *,
    unique_dispatch_id: str | None = None,
) -> dict:
    path = Path(path)
    with _exclusive_log_lock(path):
        records = _strict_records(path)
        if unique_dispatch_id and any(
            item.get("schema") == EXECUTION_RECEIPT_SCHEMA
            and str(item.get("dispatch_id") or "") == unique_dispatch_id
            for item in records
        ):
            raise ReceiptConflictError(
                f"immutable receipt already exists for dispatch_id={unique_dispatch_id}"
            )
        _validate_ledger_records([*records, record], path)
        _append_records_locked(path, [record])
    return record


def _optional_nonnegative_int(value: int | str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _optional_positive_int(value: int | str | None) -> int | None:
    parsed = _optional_nonnegative_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _execution_succeeded(record: dict) -> bool:
    """Return true only for an internally consistent successful execution."""
    if str(record.get("status") or "").strip().lower() != "completed":
        return False
    if str(record.get("error") or "").strip():
        return False
    if str(record.get("outcome") or "").strip().lower() != "ok":
        return False
    finish_reason = str(
        record.get("finish_reason") or ""
    ).strip().lower()
    return finish_reason in SUCCESSFUL_EXECUTION_FINISH


def _has_authoritative_token_usage(record: dict) -> bool:
    """Validate observed token telemetry instead of trusting a status flag."""
    if (
        record.get("actual_tokens_known") is not True
        or str(record.get("token_usage_status") or "").strip().lower()
        != "observed"
    ):
        return False
    values: list[int] = []
    for field in ("tokens_in", "tokens_out", "tokens"):
        try:
            value = int(record.get(field))
        except (TypeError, ValueError):
            return False
        if value < 0:
            return False
        values.append(value)
    return values[2] == values[0] + values[1]


def _verified_provider_observed_usage(
    record: dict,
    reservation: dict | None,
    call_start: dict | None,
) -> bool:
    """Require durable call provenance before settling observed token usage."""
    if (
        reservation is None
        or call_start is None
        or not _has_authoritative_token_usage(record)
        or str(record.get("status") or "").strip().lower()
        not in PROVIDER_RESULT_STATUSES
        or call_start.get("schema") != PROVIDER_CALL_START_SCHEMA
        or call_start.get("immutable") is not True
        or str(call_start.get("status") or "")
        != "provider_call_started"
        or str(call_start.get("dispatch_id") or "")
        != str(reservation.get("dispatch_id") or "")
        or str(call_start.get("dispatch_id") or "")
        != str(record.get("dispatch_id") or "")
        or str(call_start.get("reservation_id") or "")
        != str(reservation.get("reservation_id") or "")
        or str(call_start.get("task_id") or "")
        != str(reservation.get("task_id") or "")
        or str(call_start.get("claim_id") or "")
        != str(reservation.get("claim_id") or "")
        or str(call_start.get("reservation_fingerprint") or "")
        != _reservation_fingerprint(reservation)
        or call_start.get("budget_authority_fingerprint")
        != dict(reservation.get("budget_authority") or {}).get(
            "authority_fingerprint"
        )
        or str(record.get("budget_provider_call_start_id") or "")
        != str(call_start.get("call_start_id") or "")
    ):
        return False
    reservation_source = str(
        call_start.get("reservation_source") or ""
    ).strip()
    call_source = str(call_start.get("source") or "").strip()
    allowed_receipt_sources = PROVIDER_CALL_START_TRANSITIONS.get(
        (reservation_source, call_source)
    )
    if (
        reservation_source != str(reservation.get("source") or "").strip()
        or allowed_receipt_sources is None
        or str(record.get("source") or "").strip()
        not in allowed_receipt_sources
        or str(record.get("provider") or "").strip()
        != str(call_start.get("provider") or "").strip()
        or str(record.get("execution_surface") or "").strip()
        != str(call_start.get("execution_surface") or "").strip()
    ):
        return False
    return True


def _has_authoritative_billed_cost(record: dict) -> bool:
    """Validate billed cost telemetry and its currency."""
    if (
        str(record.get("billed_cost_status") or "").strip().lower()
        != "observed"
        or record.get("billed_cost") is None
        or not str(record.get("currency") or "").strip()
    ):
        return False
    try:
        billed_cost = float(record["billed_cost"])
    except (TypeError, ValueError):
        return False
    return math.isfinite(billed_cost) and billed_cost >= 0


def _verified_pre_provider_skip(
    record: dict,
    reservation: dict | None,
    settlement: dict | None,
) -> bool:
    """Require a reservation-bound durable no-provider-call settlement."""
    if reservation is None or settlement is None:
        return False
    reservation_source = str(reservation.get("source") or "").strip()
    receipt_source = str(record.get("source") or "").strip()
    if (
        str(record.get("status") or "").strip().lower() != "skipped"
        or str(record.get("finish_reason") or "").strip().lower()
        != "skipped"
        or (
            reservation_source,
            receipt_source,
        ) not in NO_PROVIDER_SETTLEMENT_TRANSITIONS
        or settlement.get("schema") != NO_PROVIDER_SETTLEMENT_SCHEMA
        or settlement.get("immutable") is not True
        or str(settlement.get("status") or "")
        != "released_without_provider_call"
        or str(settlement.get("dispatch_id") or "")
        != str(reservation.get("dispatch_id") or "")
        or str(settlement.get("dispatch_id") or "")
        != str(record.get("dispatch_id") or "")
        or str(settlement.get("reservation_id") or "")
        != str(reservation.get("reservation_id") or "")
        or str(settlement.get("reservation_source") or "")
        != reservation_source
        or str(settlement.get("receipt_source") or "")
        != receipt_source
        or str(settlement.get("reservation_fingerprint") or "")
        != _reservation_fingerprint(reservation)
        or settlement.get("budget_authority_fingerprint")
        != dict(reservation.get("budget_authority") or {}).get(
            "authority_fingerprint"
        )
        or str(record.get("budget_no_provider_settlement_id") or "")
        != str(settlement.get("settlement_id") or "")
    ):
        return False
    if any(
        str(record.get(field) or "").strip()
        for field in (
            "observed_provider",
            "observed_model",
            "observed_reasoning_effort",
        )
    ):
        return False
    return (
        str(record.get("token_usage_status") or "").strip().lower()
        in {"not_dispatched", "unavailable"}
        and record.get("tokens_in") is None
        and record.get("tokens_out") is None
        and int(record.get("tokens", 0) or 0) == 0
        and str(record.get("billed_cost_status") or "").strip().lower()
        == "unavailable"
        and record.get("billed_cost") is None
    )


def _budget_settlement_basis(
    record: dict,
    reservation: dict | None,
    settlement: dict | None = None,
    call_start: dict | None = None,
) -> str:
    if reservation is None:
        return "not_required_or_unreserved"
    if _verified_pre_provider_skip(record, reservation, settlement):
        return "pre_provider_skip"
    if _verified_provider_observed_usage(
        record,
        reservation,
        call_start,
    ):
        return "observed_usage"
    return "conservative_ceiling"


def _safe_record_id(value: str, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized):
        raise ReceiptIntegrityError(f"invalid {label}: {value!r}")
    return normalized


def _parse_frontmatter_scalar(path: Path, key: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReceiptIntegrityError(f"budget authority unreadable: {path}") from exc
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ReceiptIntegrityError(f"budget authority has malformed frontmatter: {path}")
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$")
    for line in parts[1].splitlines():
        match = pattern.match(line)
        if match:
            value = match.group(1).strip()
            return value if value else None
    return None


def _parse_budget_value(value, key: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ReceiptIntegrityError(f"{key} must be a non-negative integer") from exc
    if parsed < 0:
        raise ReceiptIntegrityError(f"{key} must be a non-negative integer")
    return parsed


def _budget_authority(
    *,
    root: Path,
    task_id: str,
    claim_id: str | None,
    task_token_budget,
    claim_token_budget,
) -> dict:
    explicit_task = _parse_budget_value(task_token_budget, "task_token_budget")
    explicit_claim = _parse_budget_value(claim_token_budget, "claim_token_budget")
    task = str(task_id or "").strip()
    claim = str(claim_id or "").strip() or None
    canonical_task = None
    canonical_claim = None
    source = "unconfigured"
    authority_ref = None
    authority_fingerprint = None

    if not claim:
        claim_dir = Path(root) / "agents" / "runtime" / "task_claims"
        active_claims: list[str] = []
        if claim_dir.is_dir():
            for candidate_path in sorted(claim_dir.glob("*.json")):
                try:
                    candidate = json.loads(
                        candidate_path.read_text(encoding="utf-8")
                    )
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise ReceiptIntegrityError(
                        "claim budget authority scan unreadable: "
                        f"{candidate_path}"
                    ) from exc
                if not isinstance(candidate, dict):
                    raise ReceiptIntegrityError(
                        "claim budget authority scan found a non-object: "
                        f"{candidate_path}"
                    )
                if candidate.get("schema") != "agent-runtime-task-claim/v1":
                    raise ReceiptIntegrityError(
                        "claim budget authority scan found a schema mismatch: "
                        f"{candidate_path}"
                    )
                if str(candidate.get("task_id") or "") != task:
                    continue
                candidate_status = str(
                    candidate.get("status") or ""
                ).strip().lower()
                if candidate_status not in ACTIVE_CLAIM_STATUSES:
                    continue
                candidate_id = _safe_record_id(
                    str(candidate.get("claim_id") or ""),
                    "claim_id",
                )
                if candidate_path.stem != candidate_id:
                    raise ReceiptIntegrityError(
                        "claim budget authority identity mismatch: "
                        f"{candidate_path}"
                    )
                active_claims.append(candidate_id)
        if len(active_claims) > 1:
            raise ReceiptIntegrityError(
                "multiple active claim budget authorities for "
                f"task_id={task}: {', '.join(active_claims)}"
            )
        if active_claims:
            claim = active_claims[0]

    if claim:
        safe_claim = _safe_record_id(claim, "claim_id")
        claim_path = (
            Path(root)
            / "agents"
            / "runtime"
            / "task_claims"
            / f"{safe_claim}.json"
        )
        if claim_path.is_file():
            try:
                payload = json.loads(claim_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ReceiptIntegrityError(
                    f"claim budget authority unreadable: {claim_path}"
                ) from exc
            if not isinstance(payload, dict):
                raise ReceiptIntegrityError(
                    f"claim budget authority is not an object: {claim_path}"
                )
            if payload.get("schema") != "agent-runtime-task-claim/v1":
                raise ReceiptIntegrityError(
                    f"claim budget authority schema mismatch: {claim_path}"
                )
            if str(payload.get("claim_id") or "") != safe_claim:
                raise ReceiptIntegrityError(
                    f"claim budget authority identity mismatch: {claim_path}"
                )
            if str(payload.get("task_id") or "") != task:
                raise ReceiptIntegrityError(
                    f"claim budget authority task mismatch: {claim_path}"
                )
            claim_status = str(payload.get("status") or "").strip().lower()
            if claim_status not in ACTIVE_CLAIM_STATUSES:
                raise ReceiptIntegrityError(
                    "claim budget authority is not active "
                    f"(status={claim_status or 'missing'}): {claim_path}"
                )
            canonical_task = _parse_budget_value(
                payload.get("task_token_budget"),
                "task_token_budget",
            )
            canonical_claim = _parse_budget_value(
                payload.get("claim_token_budget"),
                "claim_token_budget",
            )
            source = "claim_record"
            authority_ref = str(claim_path.relative_to(root)).replace("\\", "/")
            authority_fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "schema": payload.get("schema"),
                        "claim_id": safe_claim,
                        "task_id": task,
                        "status": claim_status,
                        "task_token_budget": canonical_task,
                        "claim_token_budget": canonical_claim,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        else:
            raise ReceiptIntegrityError(
                f"claim budget authority missing: {claim_path}"
            )

    if not claim:
        task_paths = sorted(
            (
                Path(root) / "agents"
            ).glob(f"*/tasks/{_safe_record_id(task, 'task_id')}.md")
        )
        if len(task_paths) > 1:
            raise ReceiptIntegrityError(
                f"multiple task budget authorities for task_id={task}"
            )
        if task_paths:
            canonical_task = _parse_budget_value(
                _parse_frontmatter_scalar(task_paths[0], "task_token_budget"),
                "task_token_budget",
            )
            source = "task_record"
            authority_ref = str(task_paths[0].relative_to(root)).replace("\\", "/")
            authority_fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "task_id": task,
                        "task_token_budget": canonical_task,
                        "authority_ref": authority_ref,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()

    def _effective(canonical: int | None, explicit: int | None) -> int | None:
        if canonical is None:
            return explicit
        if explicit is None:
            return canonical
        return min(canonical, explicit)

    effective_task = _effective(canonical_task, explicit_task)
    effective_claim = _effective(canonical_claim, explicit_claim)
    if source == "unconfigured" and (
        explicit_task is not None or explicit_claim is not None
    ):
        source = "explicit"
    return {
        "source": source,
        "authority_ref": authority_ref,
        "authority_fingerprint": authority_fingerprint,
        "task_id": task,
        "claim_id": claim,
        "task_token_budget": effective_task,
        "claim_token_budget": effective_claim,
        "canonical_task_token_budget": canonical_task,
        "canonical_claim_token_budget": canonical_claim,
        "explicit_task_token_budget": explicit_task,
        "explicit_claim_token_budget": explicit_claim,
        "explicit_broadening_denied": (
            canonical_task is not None
            and explicit_task is not None
            and explicit_task > canonical_task
        )
        or (
            canonical_claim is not None
            and explicit_claim is not None
            and explicit_claim > canonical_claim
        ),
    }


def _usage_from_records(
    records: list[dict],
    *,
    task_id: str,
    claim_id: str | None,
) -> dict:
    task_receipts = [
        item
        for item in records
        if item.get("schema") == EXECUTION_RECEIPT_SCHEMA
        and str(item.get("task_id") or "") == str(task_id)
    ]
    task_reservations = [
        item
        for item in records
        if item.get("schema") == BUDGET_RESERVATION_SCHEMA
        and str(item.get("task_id") or "") == str(task_id)
    ]
    task_settlements = [
        item
        for item in records
        if item.get("schema") == NO_PROVIDER_SETTLEMENT_SCHEMA
        and str(item.get("task_id") or "") == str(task_id)
    ]
    task_call_starts = [
        item
        for item in records
        if item.get("schema") == PROVIDER_CALL_START_SCHEMA
        and str(item.get("task_id") or "") == str(task_id)
    ]
    claim_receipts = (
        [
            item
            for item in task_receipts
            if str(item.get("claim_id") or "") == str(claim_id)
        ]
        if claim_id
        else []
    )
    claim_reservations = (
        [
            item
            for item in task_reservations
            if str(item.get("claim_id") or "") == str(claim_id)
        ]
        if claim_id
        else []
    )
    claim_settlements = (
        [
            item
            for item in task_settlements
            if str(item.get("claim_id") or "") == str(claim_id)
        ]
        if claim_id
        else []
    )
    claim_call_starts = (
        [
            item
            for item in task_call_starts
            if str(item.get("claim_id") or "") == str(claim_id)
        ]
        if claim_id
        else []
    )

    def _usage(
        rows: list[dict],
        reservations: list[dict],
        settlements: list[dict],
        call_starts: list[dict],
    ) -> dict:
        costs: dict[str, float] = {}
        tokens = 0
        for item in rows:
            tokens += max(0, int(item.get("tokens", 0) or 0))
            if _has_authoritative_billed_cost(item):
                currency = str(item["currency"]).upper()
                costs[currency] = costs.get(currency, 0.0) + float(
                    item["billed_cost"]
                )
        receipts_by_dispatch = {
            str(item.get("dispatch_id") or ""): item for item in rows
        }
        settlements_by_dispatch = {
            str(item.get("dispatch_id") or ""): item
            for item in settlements
        }
        call_starts_by_dispatch = {
            str(item.get("dispatch_id") or ""): item
            for item in call_starts
        }
        pending_reservations: list[dict] = []
        conservative_unobserved_tokens = 0
        conservative_settlements = 0
        pre_provider_releases = 0
        for reservation in reservations:
            receipt = receipts_by_dispatch.get(
                str(reservation.get("dispatch_id") or "")
            )
            if receipt is None:
                pending_reservations.append(reservation)
                continue
            settlement = settlements_by_dispatch.get(
                str(reservation.get("dispatch_id") or "")
            )
            call_start = call_starts_by_dispatch.get(
                str(reservation.get("dispatch_id") or "")
            )
            basis = _budget_settlement_basis(
                receipt,
                reservation,
                settlement,
                call_start,
            )
            if basis == "pre_provider_skip":
                pre_provider_releases += 1
                continue
            if basis == "observed_usage":
                continue
            conservative_settlements += 1
            reserved = max(
                0,
                int(reservation.get("reserved_tokens", 0) or 0),
            )
            recorded = max(0, int(receipt.get("tokens", 0) or 0))
            conservative_unobserved_tokens += max(0, reserved - recorded)
        reserved_tokens = sum(
            max(0, int(item.get("reserved_tokens", 0) or 0))
            for item in pending_reservations
        )
        return {
            "receipts": len(rows),
            "tokens": tokens,
            "pending_reservations": len(pending_reservations),
            "reserved_tokens": reserved_tokens,
            "conservative_settlements": conservative_settlements,
            "conservative_unobserved_tokens": (
                conservative_unobserved_tokens
            ),
            "pre_provider_releases": pre_provider_releases,
            "committed_tokens": (
                tokens
                + reserved_tokens
                + conservative_unobserved_tokens
            ),
            "billed_cost_by_currency": {
                key: round(value, 9) for key, value in sorted(costs.items())
            },
        }

    return {
        "task_id": str(task_id),
        "claim_id": str(claim_id or "") or None,
        "task": _usage(
            task_receipts,
            task_reservations,
            task_settlements,
            task_call_starts,
        ),
        "claim": _usage(
            claim_receipts,
            claim_reservations,
            claim_settlements,
            claim_call_starts,
        ),
    }


def cumulative_usage(
    *,
    path: Path = EVAL_LOG,
    task_id: str,
    claim_id: str | None = None,
) -> dict:
    """Read durable observed usage for one task and optional claim."""
    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
    return _usage_from_records(
        records,
        task_id=str(task_id),
        claim_id=str(claim_id or "") or None,
    )


def _budget_preflight_from_records(
    records: list[dict],
    *,
    path: Path,
    root: Path,
    task_id: str,
    claim_id: str | None,
    dispatch_id: str,
    dispatch_ceiling: int | None,
    task_token_budget,
    claim_token_budget,
) -> dict:
    if any(
        str(item.get("dispatch_id") or "") == str(dispatch_id)
        for item in records
    ):
        return {
            "allowed": False,
            "reason": "duplicate_dispatch_id",
            "dispatch_id": str(dispatch_id),
        }
    for field, value in (
        ("task_token_budget", task_token_budget),
        ("claim_token_budget", claim_token_budget),
    ):
        if value in (None, ""):
            continue
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return {
                "allowed": False,
                "reason": f"invalid_{field}",
                "dispatch_id": str(dispatch_id),
            }
        if parsed < 0:
            return {
                "allowed": False,
                "reason": f"invalid_{field}",
                "dispatch_id": str(dispatch_id),
            }
    authority = _budget_authority(
        root=Path(root),
        task_id=str(task_id),
        claim_id=str(claim_id or "").strip() or None,
        task_token_budget=task_token_budget,
        claim_token_budget=claim_token_budget,
    )
    task_limit = authority["task_token_budget"]
    claim_limit = authority["claim_token_budget"]
    effective_claim_id = (
        str(authority.get("claim_id") or "").strip() or None
    )
    ceiling = _optional_positive_int(dispatch_ceiling)
    configured = task_limit is not None or claim_limit is not None
    if configured and ceiling is None:
        return {
            "allowed": False,
            "reason": "dispatch_ceiling_unavailable",
            "dispatch_id": str(dispatch_id),
            "task_token_budget": task_limit,
            "claim_token_budget": claim_limit,
            "budget_authority": authority,
        }
    usage = _usage_from_records(
        records,
        task_id=str(task_id),
        claim_id=effective_claim_id,
    )
    task_used = int(usage["task"]["tokens"])
    task_reserved = int(usage["task"]["reserved_tokens"])
    task_conservative = int(
        usage["task"]["conservative_unobserved_tokens"]
    )
    task_committed = int(usage["task"]["committed_tokens"])
    claim_used = int(usage["claim"]["tokens"])
    claim_reserved = int(usage["claim"]["reserved_tokens"])
    claim_conservative = int(
        usage["claim"]["conservative_unobserved_tokens"]
    )
    claim_committed = int(usage["claim"]["committed_tokens"])
    requested = int(ceiling or 0)
    if task_limit is not None and task_committed + requested > task_limit:
        reason = "task_budget_insufficient"
        allowed = False
    elif claim_limit is not None and claim_committed + requested > claim_limit:
        reason = "claim_budget_insufficient"
        allowed = False
    else:
        reason = "within_budget"
        allowed = True
    return {
        "allowed": allowed,
        "reason": reason,
        "dispatch_id": str(dispatch_id),
        "claim_id": effective_claim_id,
        "dispatch_ceiling": ceiling,
        "task_token_budget": task_limit,
        "task_tokens_used": task_used,
        "task_tokens_reserved": task_reserved,
        "task_tokens_conservative_unobserved": task_conservative,
        "task_tokens_committed": task_committed,
        "task_tokens_remaining": (
            max(0, task_limit - task_committed)
            if task_limit is not None
            else None
        ),
        "claim_token_budget": claim_limit,
        "claim_tokens_used": claim_used,
        "claim_tokens_reserved": claim_reserved,
        "claim_tokens_conservative_unobserved": claim_conservative,
        "claim_tokens_committed": claim_committed,
        "claim_tokens_remaining": (
            max(0, claim_limit - claim_committed)
            if claim_limit is not None
            else None
        ),
        "budget_authority": authority,
    }


def budget_preflight(
    *,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
    task_id: str,
    claim_id: str | None,
    dispatch_id: str,
    dispatch_ceiling: int | None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
) -> dict:
    """Read-only budget decision. Execution surfaces must reserve atomically."""
    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        return _budget_preflight_from_records(
            records,
            path=ledger_path,
            root=Path(root),
            task_id=str(task_id),
            claim_id=str(claim_id or "").strip() or None,
            dispatch_id=str(dispatch_id),
            dispatch_ceiling=dispatch_ceiling,
            task_token_budget=task_token_budget,
            claim_token_budget=claim_token_budget,
        )


def reserve_dispatch_budgets(
    requests: list[dict],
    *,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
    source: str = "execution_preflight",
    _commit: bool = True,
) -> dict:
    """Atomically reserve a batch of dispatch ceilings or reserve none."""
    if not requests:
        raise ValueError("at least one dispatch reservation is required")
    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        working = list(records)
        results: list[dict] = []
        reservations: list[dict] = []
        for request in requests:
            dispatch_id = str(request.get("dispatch_id") or "").strip()
            task_id = str(request.get("task_id") or "").strip()
            if not dispatch_id or not task_id:
                raise ValueError("dispatch_id and task_id are required")
            result = _budget_preflight_from_records(
                working,
                path=ledger_path,
                root=Path(request.get("root") or root),
                task_id=task_id,
                claim_id=str(request.get("claim_id") or "").strip() or None,
                dispatch_id=dispatch_id,
                dispatch_ceiling=request.get("dispatch_ceiling"),
                task_token_budget=request.get("task_token_budget"),
                claim_token_budget=request.get("claim_token_budget"),
            )
            results.append(result)
            if result["allowed"]:
                reservation_id = "reservation-" + hashlib.sha256(
                    dispatch_id.encode("utf-8")
                ).hexdigest()[:24]
                reservation = {
                    "schema": BUDGET_RESERVATION_SCHEMA,
                    "immutable": True,
                    "reservation_id": reservation_id,
                    "ts": datetime.now().astimezone().isoformat(
                        timespec="seconds"
                    ),
                    "dispatch_id": dispatch_id,
                    "task_id": task_id,
                    "claim_id": (
                        str(
                            (
                                result.get("budget_authority") or {}
                            ).get("claim_id")
                            or ""
                        ).strip()
                        or None
                    ),
                    "reserved_tokens": int(result.get("dispatch_ceiling") or 0),
                    "source": str(source or "execution_preflight"),
                    "task_token_budget": result.get("task_token_budget"),
                    "claim_token_budget": result.get("claim_token_budget"),
                    "budget_authority": dict(
                        result.get("budget_authority") or {}
                    ),
                }
                result["reservation_id"] = reservation_id
                result["reservation_status"] = (
                    "pending" if _commit else "planned"
                )
                reservations.append(reservation)
                working.append(reservation)

        allowed = all(result["allowed"] for result in results)
        if allowed:
            if _commit:
                _validate_ledger_records(working, ledger_path)
                _append_records_locked(ledger_path, reservations)
        else:
            for result in results:
                result["batch_allowed"] = False
                if result["allowed"]:
                    result["batch_reason"] = "batch_budget_denied"
                result.pop("reservation_id", None)
                result["reservation_status"] = "not_reserved"
        return {
            "allowed": allowed,
            "results": results,
            "reservations": reservations if allowed else [],
        }


def plan_dispatch_budgets(
    requests: list[dict],
    *,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
    source: str = "execution_preflight_dry_run",
) -> dict:
    """Evaluate a batch with reservation semantics without mutating the ledger."""
    return reserve_dispatch_budgets(
        requests,
        path=path,
        root=root,
        source=source,
        _commit=False,
    )


def reserve_dispatch_budget(
    *,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
    task_id: str,
    claim_id: str | None,
    dispatch_id: str,
    dispatch_ceiling: int | None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
    source: str = "execution_preflight",
) -> dict:
    batch = reserve_dispatch_budgets(
        [
            {
                "task_id": task_id,
                "claim_id": claim_id,
                "dispatch_id": dispatch_id,
                "dispatch_ceiling": dispatch_ceiling,
                "task_token_budget": task_token_budget,
                "claim_token_budget": claim_token_budget,
            }
        ],
        path=path,
        root=root,
        source=source,
    )
    return batch["results"][0]


def validate_dispatch_reservation(
    *,
    dispatch_id: str,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
) -> dict:
    """Revalidate a pending reservation and its canonical authority pre-spawn."""
    ledger_path = Path(path)
    dispatch = str(dispatch_id or "").strip()
    if not dispatch:
        raise ValueError("dispatch_id is required")
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        receipt = next(
            (
                item
                for item in records
                if item.get("schema") == EXECUTION_RECEIPT_SCHEMA
                and str(item.get("dispatch_id") or "") == dispatch
            ),
            None,
        )
        if receipt is not None:
            return {
                "authorized": False,
                "reason": "dispatch_already_terminal",
                "dispatch_id": dispatch,
                "receipt_id": receipt.get("receipt_id"),
            }
        reservation = next(
            (
                item
                for item in records
                if item.get("schema") == BUDGET_RESERVATION_SCHEMA
                and str(item.get("dispatch_id") or "") == dispatch
            ),
            None,
        )
        if reservation is None:
            return {
                "authorized": False,
                "reason": "reservation_missing",
                "dispatch_id": dispatch,
            }
        authority = _budget_authority(
            root=Path(root),
            task_id=str(reservation.get("task_id") or ""),
            claim_id=str(reservation.get("claim_id") or "").strip() or None,
            task_token_budget=reservation.get("task_token_budget"),
            claim_token_budget=reservation.get("claim_token_budget"),
        )
        reserved_authority = dict(reservation.get("budget_authority") or {})
        if authority.get("authority_fingerprint") != reserved_authority.get(
            "authority_fingerprint"
        ):
            return {
                "authorized": False,
                "reason": "budget_authority_changed",
                "dispatch_id": dispatch,
                "reservation_id": reservation.get("reservation_id"),
                "reserved_authority_fingerprint": reserved_authority.get(
                    "authority_fingerprint"
                ),
                "current_authority_fingerprint": authority.get(
                    "authority_fingerprint"
                ),
            }
        return {
            "authorized": True,
            "reason": "pending_reservation_authorized",
            "dispatch_id": dispatch,
            "reservation_id": reservation.get("reservation_id"),
            "task_id": reservation.get("task_id"),
            "claim_id": reservation.get("claim_id"),
            "budget_authority": authority,
        }


def record_provider_call_start(
    *,
    dispatch_id: str,
    task_id: str,
    source: str,
    provider: str,
    execution_surface: str,
    path: Path = EVAL_LOG,
    root: Path = ROOT,
    timestamp: str | None = None,
) -> dict:
    """Durably bind a pending reservation immediately before a provider call."""
    dispatch = str(dispatch_id or "").strip()
    task = str(task_id or "").strip()
    call_source = str(source or "").strip()
    configured_provider = str(provider or "").strip()
    surface = str(execution_surface or "").strip()
    if not dispatch or not task:
        raise ValueError("dispatch_id and task_id are required")
    if not configured_provider or not surface:
        raise ValueError("provider and execution_surface are required")

    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        reservation = next(
            (
                item
                for item in records
                if item.get("schema") == BUDGET_RESERVATION_SCHEMA
                and str(item.get("dispatch_id") or "") == dispatch
            ),
            None,
        )
        if reservation is None:
            raise ReceiptIntegrityError(
                "provider call-start requires a matching pending "
                f"reservation for dispatch_id={dispatch}"
            )
        if str(reservation.get("task_id") or "") != task:
            raise ReceiptIntegrityError(
                "provider call-start task differs from reservation "
                f"for dispatch_id={dispatch}"
            )
        reservation_source = str(
            reservation.get("source") or ""
        ).strip()
        if (
            reservation_source,
            call_source,
        ) not in PROVIDER_CALL_START_TRANSITIONS:
            raise ReceiptIntegrityError(
                "invalid provider call-start transition "
                f"{reservation_source}->{call_source} for "
                f"dispatch_id={dispatch}"
            )
        current_authority = _budget_authority(
            root=Path(root),
            task_id=task,
            claim_id=str(
                reservation.get("claim_id") or ""
            ).strip()
            or None,
            task_token_budget=reservation.get("task_token_budget"),
            claim_token_budget=reservation.get("claim_token_budget"),
        )
        reserved_authority = dict(
            reservation.get("budget_authority") or {}
        )
        if current_authority.get(
            "authority_fingerprint"
        ) != reserved_authority.get("authority_fingerprint"):
            raise ReceiptIntegrityError(
                "provider call-start budget authority changed for "
                f"dispatch_id={dispatch}"
            )

        reservation_id = str(reservation.get("reservation_id") or "")
        call_start_id = _provider_call_start_id(
            reservation_id,
            call_source,
            configured_provider,
            surface,
        )
        expected = {
            "schema": PROVIDER_CALL_START_SCHEMA,
            "immutable": True,
            "call_start_id": call_start_id,
            "dispatch_id": dispatch,
            "task_id": task,
            "claim_id": reservation.get("claim_id"),
            "reservation_id": reservation_id,
            "reservation_source": reservation_source,
            "source": call_source,
            "status": "provider_call_started",
            "provider": configured_provider,
            "execution_surface": surface,
            "reservation_fingerprint": _reservation_fingerprint(
                reservation
            ),
            "budget_authority_fingerprint": reserved_authority.get(
                "authority_fingerprint"
            ),
        }
        existing = next(
            (
                item
                for item in records
                if item.get("schema") == PROVIDER_CALL_START_SCHEMA
                and str(item.get("dispatch_id") or "") == dispatch
            ),
            None,
        )
        if existing is not None:
            if all(existing.get(key) == value for key, value in expected.items()):
                return existing
            raise ReceiptConflictError(
                "immutable provider call-start already exists for "
                f"dispatch_id={dispatch}"
            )
        if any(
            item.get("schema") == EXECUTION_RECEIPT_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
            for item in records
        ):
            raise ReceiptConflictError(
                "provider call-start cannot follow terminal receipt for "
                f"dispatch_id={dispatch}"
            )
        if any(
            item.get("schema") == NO_PROVIDER_SETTLEMENT_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
            for item in records
        ):
            raise ReceiptConflictError(
                "provider call-start conflicts with no-provider settlement "
                f"for dispatch_id={dispatch}"
            )
        marker = {
            **expected,
            "ts": timestamp
            or datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        _validate_ledger_records([*records, marker], ledger_path)
        _append_records_locked(ledger_path, [marker])
    return marker


def record_execution_receipt(
    *,
    dispatch_id: str,
    task_id: str,
    source: str,
    status: str,
    claim_id: str | None = None,
    role: str | None = None,
    workload_id: str | None = None,
    provider: str | None = None,
    execution_surface: str | None = None,
    requested_tier: str | None = None,
    selected_tier: str | None = None,
    resolved_model: str | None = None,
    resolved_reasoning_effort: str | None = None,
    resolved_model_source: str | None = None,
    resolved_reasoning_source: str | None = None,
    observed_provider: str | None = None,
    observed_model: str | None = None,
    observed_reasoning_effort: str | None = None,
    token_usage_status: str | None = None,
    tokens_in: int | str | None = None,
    tokens_out: int | str | None = None,
    billed_cost_status: str | None = None,
    billed_cost: float | None = None,
    currency: str | None = None,
    finish_reason: str | None = None,
    error: str | None = None,
    route_status: str | None = None,
    application_status: str | None = None,
    model_changed: bool | None = None,
    route_changed: bool | None = None,
    baseline_receipt_id: str | None = None,
    baseline_model: str | None = None,
    baseline_reasoning_effort: str | None = None,
    baseline_observation_status: str | None = None,
    baseline_tokens: int | None = None,
    baseline_billed_cost: float | None = None,
    baseline_currency: str | None = None,
    grade: str | None = None,
    policy_model: str | None = None,
    selected_model: str | None = None,
    routing_signals: list[str] | None = None,
    budget_preflight_result: dict | None = None,
    path: Path = EVAL_LOG,
    timestamp: str | None = None,
    _existing_records: list[dict] | None = None,
) -> dict:
    """Append exactly one immutable execution receipt for a dispatch."""
    dispatch = str(dispatch_id or "").strip()
    if not dispatch:
        raise ValueError("dispatch_id is required")
    task = str(task_id or "").strip()
    if not task:
        raise ValueError("task_id is required")
    receipt_id = "receipt-" + hashlib.sha256(
        dispatch.encode("utf-8")
    ).hexdigest()[:24]
    in_tokens = _optional_nonnegative_int(tokens_in)
    out_tokens = _optional_nonnegative_int(tokens_out)
    derived_token_status = (
        "observed"
        if in_tokens is not None and out_tokens is not None
        else "partial"
        if in_tokens is not None or out_tokens is not None
        else "unavailable"
    )
    actual_currency = str(currency or "").strip().upper() or None
    actual_cost = None
    if billed_cost is not None:
        actual_cost = float(billed_cost)
        if not math.isfinite(actual_cost) or actual_cost < 0:
            raise ValueError("billed_cost must be non-negative")
        if actual_currency is None:
            raise ValueError("currency is required when billed_cost is supplied")
    cost_status = str(billed_cost_status or "").strip() or (
        "observed" if actual_cost is not None else "unavailable"
    )
    baseline_currency_value = (
        str(baseline_currency or "").strip().upper() or None
    )
    baseline_cost = None
    if baseline_billed_cost is not None:
        baseline_cost = float(baseline_billed_cost)
        if not math.isfinite(baseline_cost) or baseline_cost < 0:
            raise ValueError("baseline_billed_cost must be non-negative")
        if baseline_currency_value is None:
            raise ValueError(
                "baseline_currency is required when baseline_billed_cost is supplied"
            )
    token_status = str(token_usage_status or derived_token_status)
    tokens = int(in_tokens or 0) + int(out_tokens or 0)
    rec = {
        "schema": EXECUTION_RECEIPT_SCHEMA,
        "immutable": True,
        "receipt_id": receipt_id,
        "ts": timestamp
        or datetime.now().astimezone().isoformat(timespec="seconds"),
        "dispatch_id": dispatch,
        "task_id": task,
        "claim_id": str(claim_id or "").strip() or None,
        "role": str(role or "").strip() or None,
        "workload_id": str(workload_id or "").strip() or None,
        "provider": str(provider or "").strip() or None,
        "execution_surface": str(execution_surface or "").strip() or None,
        "requested_tier": str(requested_tier or "").strip() or None,
        "selected_tier": str(selected_tier or "").strip() or None,
        "resolved_model": str(resolved_model or "").strip() or None,
        "resolved_reasoning_effort": (
            str(resolved_reasoning_effort or "").strip() or None
        ),
        "resolved_model_source": (
            str(resolved_model_source or "").strip() or "unavailable"
        ),
        "resolved_reasoning_source": (
            str(resolved_reasoning_source or "").strip() or "unavailable"
        ),
        "observed_provider": str(observed_provider or "").strip() or None,
        "observed_model": str(observed_model or "").strip() or None,
        "observed_reasoning_effort": (
            str(observed_reasoning_effort or "").strip() or None
        ),
        "model_observation_status": (
            "observed" if str(observed_model or "").strip() else "unverified"
        ),
        "token_usage_status": token_status,
        "tokens_in": in_tokens,
        "tokens_out": out_tokens,
        "tokens": tokens,
        "actual_tokens_known": token_status == "observed",
        "billed_cost_status": cost_status,
        "billed_cost": actual_cost,
        "currency": actual_currency,
        "source": str(source or "").strip() or "unavailable",
        "status": str(status or "").strip() or "unknown",
        "finish_reason": (
            None if finish_reason is None else str(finish_reason)
        ),
        "outcome": "ok" if not error else "gate-error",
        "error": str(error or "").strip() or None,
        "route_status": route_status,
        "application_status": application_status,
        "model_changed": model_changed,
        "route_changed": route_changed,
        "baseline_receipt_id": (
            str(baseline_receipt_id or "").strip() or None
        ),
        "baseline_model": str(baseline_model or "").strip() or None,
        "baseline_reasoning_effort": (
            str(baseline_reasoning_effort or "").strip() or None
        ),
        "baseline_observation_status": (
            str(baseline_observation_status or "").strip() or "unavailable"
        ),
        "baseline_tokens": _optional_nonnegative_int(baseline_tokens),
        "baseline_billed_cost": baseline_cost,
        "baseline_currency": baseline_currency_value,
        "grade": str(grade or "?"),
        "model": (
            str(observed_model or "").strip()
            or str(resolved_model or "").strip()
            or "unverified"
        ),
        "policy_model": policy_model,
        "selected_model": selected_model,
        "routing_signals": list(routing_signals or []),
        "budget_preflight": dict(budget_preflight_result or {}),
    }
    ledger_path = Path(path)
    if _existing_records is not None:
        return _finalize_execution_receipt(
            rec,
            list(_existing_records),
            ledger_path,
        )
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        rec = _finalize_execution_receipt(rec, records, ledger_path)
        _validate_ledger_records([*records, rec], ledger_path)
        _append_records_locked(ledger_path, [rec])
    return rec


def record_pre_provider_skip_receipt(
    *,
    dispatch_id: str,
    task_id: str,
    source: str,
    path: Path = EVAL_LOG,
    **receipt_fields,
) -> dict:
    """Atomically prove one reserved dispatch ended before provider start."""
    values = dict(receipt_fields)
    if "_existing_records" in values:
        raise ValueError("_existing_records is internal")
    status = str(values.pop("status", "skipped") or "").strip().lower()
    finish_reason = str(
        values.pop("finish_reason", "skipped") or ""
    ).strip().lower()
    if status != "skipped" or finish_reason != "skipped":
        raise ValueError(
            "pre-provider settlement requires skipped status and finish"
        )
    dispatch = str(dispatch_id or "").strip()
    task = str(task_id or "").strip()
    receipt_source = str(source or "").strip()
    if not dispatch or not task:
        raise ValueError("dispatch_id and task_id are required")

    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        if any(
            item.get("schema") == EXECUTION_RECEIPT_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
            for item in records
        ):
            raise ReceiptConflictError(
                f"immutable receipt already exists for dispatch_id={dispatch}"
            )
        if any(
            item.get("schema") == NO_PROVIDER_SETTLEMENT_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
            for item in records
        ):
            raise ReceiptConflictError(
                "immutable no-provider settlement already exists for "
                f"dispatch_id={dispatch}"
            )
        if any(
            item.get("schema") == PROVIDER_CALL_START_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
            for item in records
        ):
            raise ReceiptConflictError(
                "no-provider settlement conflicts with provider call-start "
                f"for dispatch_id={dispatch}"
            )
        reservation = next(
            (
                item
                for item in records
                if item.get("schema") == BUDGET_RESERVATION_SCHEMA
                and str(item.get("dispatch_id") or "") == dispatch
            ),
            None,
        )
        if reservation is None:
            raise ReceiptIntegrityError(
                "pre-provider settlement requires a matching pending "
                f"reservation for dispatch_id={dispatch}"
            )
        reservation_source = str(
            reservation.get("source") or ""
        ).strip()
        if (
            reservation_source,
            receipt_source,
        ) not in NO_PROVIDER_SETTLEMENT_TRANSITIONS:
            raise ReceiptIntegrityError(
                "invalid no-provider settlement transition "
                f"{reservation_source}->{receipt_source} for "
                f"dispatch_id={dispatch}"
            )
        if str(reservation.get("task_id") or "") != task:
            raise ReceiptIntegrityError(
                "pre-provider settlement task differs from reservation "
                f"for dispatch_id={dispatch}"
            )

        timestamp = str(
            values.get("timestamp")
            or datetime.now().astimezone().isoformat(timespec="seconds")
        )
        values["timestamp"] = timestamp
        reservation_id = str(reservation.get("reservation_id") or "")
        settlement_id = "no-provider-settlement-" + hashlib.sha256(
            f"{reservation_id}:{receipt_source}".encode("utf-8")
        ).hexdigest()[:24]
        settlement = {
            "schema": NO_PROVIDER_SETTLEMENT_SCHEMA,
            "immutable": True,
            "settlement_id": settlement_id,
            "ts": timestamp,
            "dispatch_id": dispatch,
            "task_id": task,
            "claim_id": reservation.get("claim_id"),
            "reservation_id": reservation_id,
            "reservation_source": reservation_source,
            "receipt_source": receipt_source,
            "status": "released_without_provider_call",
            "reservation_fingerprint": _reservation_fingerprint(
                reservation
            ),
            "budget_authority_fingerprint": dict(
                reservation.get("budget_authority") or {}
            ).get("authority_fingerprint"),
        }
        rec = record_execution_receipt(
            dispatch_id=dispatch,
            task_id=task,
            source=receipt_source,
            status="skipped",
            finish_reason="skipped",
            path=ledger_path,
            _existing_records=[*records, settlement],
            **values,
        )
        combined = [*records, settlement, rec]
        _validate_ledger_records(combined, ledger_path)
        _append_records_locked(ledger_path, [settlement, rec])
    return rec


def _route_observation_complete(record: dict) -> bool:
    """Require every supported route-identity dimension to be observed."""
    if not str(record.get("observed_model") or "").strip():
        return False
    configured_identity = model_routing.canonical_provider_identity(
        record.get("provider")
    )
    observed_identity = model_routing.canonical_provider_identity(
        record.get("observed_provider")
    )
    if (
        configured_identity is None
        or observed_identity is None
        or configured_identity != observed_identity
    ):
        return False

    if str(record.get("observed_reasoning_effort") or "").strip():
        return True
    if str(record.get("resolved_reasoning_effort") or "").strip():
        return False

    reasoning_source = str(
        record.get("resolved_reasoning_source") or ""
    ).strip().lower()
    return (
        reasoning_source == "unsupported"
        and model_routing.provider_reasoning_capability(configured_identity)
        == "unsupported"
    )


def _finalize_execution_receipt(
    rec: dict,
    records: list[dict],
    ledger_path: Path,
) -> dict:
    dispatch = str(rec.get("dispatch_id") or "")
    if any(
        item.get("schema") == EXECUTION_RECEIPT_SCHEMA
        and str(item.get("dispatch_id") or "") == dispatch
        for item in records
    ):
        raise ReceiptConflictError(
            f"immutable receipt already exists for dispatch_id={dispatch}"
        )

    reservation = next(
        (
            item
            for item in records
            if item.get("schema") == BUDGET_RESERVATION_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
        ),
        None,
    )
    settlement = next(
        (
            item
            for item in records
            if item.get("schema") == NO_PROVIDER_SETTLEMENT_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
        ),
        None,
    )
    call_start = next(
        (
            item
            for item in records
            if item.get("schema") == PROVIDER_CALL_START_SCHEMA
            and str(item.get("dispatch_id") or "") == dispatch
        ),
        None,
    )
    preflight_authority = dict(
        (rec.get("budget_preflight") or {}).get("budget_authority") or {}
    )
    authoritative_claim = str(
        (reservation or {}).get("claim_id")
        or preflight_authority.get("claim_id")
        or ""
    ).strip() or None
    if authoritative_claim:
        supplied_claim = str(rec.get("claim_id") or "").strip() or None
        if supplied_claim and supplied_claim != authoritative_claim:
            raise ReceiptIntegrityError(
                "execution receipt claim differs from reserved budget "
                f"authority for dispatch_id={dispatch}"
            )
        rec["claim_id"] = authoritative_claim

    actual_execution_succeeded = _execution_succeeded(rec)
    baseline_id = str(rec.get("baseline_receipt_id") or "").strip() or None
    baseline = next(
        (
            item
            for item in records
            if item.get("schema") == EXECUTION_RECEIPT_SCHEMA
            and str(item.get("receipt_id") or "") == str(baseline_id or "")
        ),
        None,
    )
    def _clear_unverified_baseline() -> None:
        rec["baseline_model"] = None
        rec["baseline_reasoning_effort"] = None
        rec["baseline_observation_status"] = "unavailable"
        rec["baseline_tokens"] = None
        rec["baseline_billed_cost"] = None
        rec["baseline_currency"] = None

    if baseline_id is None:
        rec["baseline_reference_status"] = "unavailable"
        rec["baseline_reference_reason"] = "baseline_receipt_id_missing"
        _clear_unverified_baseline()
    elif baseline is None:
        rec["baseline_reference_status"] = "invalid"
        rec["baseline_reference_reason"] = "baseline_receipt_unavailable"
        _clear_unverified_baseline()
    elif (
        not rec["workload_id"]
        or str(baseline.get("workload_id") or "") != rec["workload_id"]
    ):
        rec["baseline_reference_status"] = "invalid"
        rec["baseline_reference_reason"] = "workload_identity_mismatch"
        _clear_unverified_baseline()
    elif not _execution_succeeded(baseline):
        rec["baseline_reference_status"] = "invalid"
        rec["baseline_reference_reason"] = (
            "baseline_execution_not_successful"
        )
        _clear_unverified_baseline()
    elif (
        not str(baseline.get("observed_model") or "").strip()
        or not _has_authoritative_token_usage(baseline)
    ):
        rec["baseline_reference_status"] = "invalid"
        rec["baseline_reference_reason"] = "baseline_not_observed"
        _clear_unverified_baseline()
    elif not _route_observation_complete(baseline):
        rec["baseline_reference_status"] = "invalid"
        rec["baseline_reference_reason"] = (
            "baseline_route_observation_incomplete"
        )
        _clear_unverified_baseline()
    else:
        rec["baseline_reference_status"] = "verified"
        rec["baseline_reference_reason"] = None
        rec["baseline_model"] = baseline.get("observed_model")
        rec["baseline_reasoning_effort"] = baseline.get(
            "observed_reasoning_effort"
        )
        rec["baseline_observation_status"] = "observed"
        rec["baseline_tokens"] = int(baseline.get("tokens", 0) or 0)
        rec["baseline_billed_cost"] = baseline.get("billed_cost")
        rec["baseline_currency"] = baseline.get("currency")

        def _route_identity(model, reasoning):
            normalized_model = str(model or "").strip()
            if not normalized_model:
                return None
            normalized_reasoning = (
                str(reasoning or "").strip().lower() or None
            )
            return normalized_model, normalized_reasoning

        actual_identity = _route_identity(
            rec.get("observed_model"),
            rec.get("observed_reasoning_effort"),
        )
        baseline_identity = _route_identity(
            baseline.get("observed_model"),
            baseline.get("observed_reasoning_effort"),
        )
        resolved_identity = _route_identity(
            rec.get("resolved_model"),
            rec.get("resolved_reasoning_effort"),
        )
        if (
            not actual_execution_succeeded
            or resolved_identity is None
            or actual_identity is None
            or not _route_observation_complete(rec)
        ):
            rec["application_status"] = "unverified"
        else:
            rec["application_status"] = (
                "applied"
                if actual_identity == resolved_identity
                else "not_applied"
            )

        if actual_identity is None or baseline_identity is None:
            rec["model_changed"] = None
            rec["route_changed"] = None
            rec["route_status"] = "unverified"
        else:
            rec["model_changed"] = (
                actual_identity[0] != baseline_identity[0]
            )
            rec["route_changed"] = actual_identity != baseline_identity
            if not actual_execution_succeeded:
                rec["route_status"] = "unverified"
            elif rec["route_changed"] is False:
                rec["route_status"] = "ineffective_equivalent"
            elif rec["application_status"] == "applied":
                rec["route_status"] = "effective"
            elif rec["application_status"] == "not_applied":
                rec["route_status"] = "not_applied"
            else:
                rec["route_status"] = "unverified"

    if not actual_execution_succeeded:
        rec["application_status"] = "unverified"
        rec["route_status"] = "unverified"
    rec["budget_reservation_id"] = (
        reservation.get("reservation_id") if reservation else None
    )
    rec["budget_no_provider_settlement_id"] = (
        settlement.get("settlement_id") if settlement else None
    )
    rec["budget_provider_call_start_id"] = (
        call_start.get("call_start_id") if call_start else None
    )
    rec["budget_reservation_status"] = (
        "settled" if reservation else "not_required_or_unreserved"
    )
    rec["budget_settlement_basis"] = _budget_settlement_basis(
        rec,
        reservation,
        settlement,
        call_start,
    )
    return rec


def record_execution_receipts(
    receipts: list[dict],
    *,
    path: Path = EVAL_LOG,
) -> list[dict]:
    """Atomically append a batch of terminal receipts, or append none."""
    if not receipts:
        raise ValueError("at least one execution receipt is required")
    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
        working = list(records)
        prepared: list[dict] = []
        for raw in receipts:
            values = dict(raw)
            if "path" in values or "_existing_records" in values:
                raise ValueError(
                    "batch receipt entries may not override path/internal state"
                )
            rec = record_execution_receipt(
                **values,
                path=ledger_path,
                _existing_records=working,
            )
            prepared.append(rec)
            working.append(rec)
        _validate_ledger_records(working, ledger_path)
        _append_records_locked(ledger_path, prepared)
    return prepared


def record_outcome(task_id: str, grade: str, model: str, tokens: int,
                   finish_reason: str = "stop", outcome: str | None = None,
                   path: Path = EVAL_LOG, policy_model: str | None = None,
                   selected_model: str | None = None,
                   routing_signals: list[str] | None = None,
                   baseline_tokens: int | None = None,
                   actual_tokens_known: bool | None = None,
                   baseline_verdict: str | None = None,
                   collab_verdict: str | None = None,
                   collab_members: list[str] | None = None,
                   provider: str | None = None,
                   requested_tier: str | None = None,
                   resolved_model: str | None = None,
                   observed_model: str | None = None,
                   model_changed: bool | None = None,
                   route_status: str | None = None,
                   application_status: str | None = None,
                   baseline_model: str | None = None,
                   billed_cost: float | None = None,
                   currency: str | None = None,
                   baseline_billed_cost: float | None = None,
                   baseline_currency: str | None = None) -> dict:
    rec = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),  # tz-aware(reviewer #3)
           "task_id": task_id, "grade": grade,
           "model": model, "tokens": int(tokens), "finish_reason": finish_reason,
           "outcome": "ok" if outcome is None else outcome}  # None 만 ok(빈 문자열 보존, reviewer #2)
    if policy_model is not None:
        rec["policy_model"] = policy_model
    if selected_model is not None:
        rec["selected_model"] = selected_model
    if routing_signals is not None:
        rec["routing_signals"] = list(routing_signals)
    if baseline_tokens is not None:
        rec["baseline_tokens"] = int(baseline_tokens)
    if actual_tokens_known is not None:
        rec["actual_tokens_known"] = bool(actual_tokens_known)
    if baseline_verdict is not None:
        rec["baseline_verdict"] = baseline_verdict
    if collab_verdict is not None:
        rec["collab_verdict"] = collab_verdict
    if collab_members is not None:
        rec["collab_members"] = list(collab_members)
    optional = {
        "provider": provider,
        "requested_tier": requested_tier,
        "resolved_model": resolved_model,
        "observed_model": observed_model,
        "model_changed": model_changed,
        "route_status": route_status,
        "application_status": application_status,
        "baseline_model": baseline_model,
    }
    for key, value in optional.items():
        if value is not None:
            rec[key] = value
    actual_currency = str(currency or "").strip().upper() or None
    baseline_cost_currency = str(baseline_currency or "").strip().upper() or None
    if billed_cost is not None:
        if actual_currency is None:
            raise ValueError("currency is required when billed_cost is supplied")
        actual_cost = float(billed_cost)
        if not math.isfinite(actual_cost) or actual_cost < 0:
            raise ValueError("billed_cost must be non-negative")
        rec["billed_cost"] = actual_cost
        rec["currency"] = actual_currency
    if baseline_billed_cost is not None:
        if baseline_cost_currency is None:
            raise ValueError(
                "baseline_currency is required when baseline_billed_cost is supplied"
            )
        baseline_cost = float(baseline_billed_cost)
        if not math.isfinite(baseline_cost) or baseline_cost < 0:
            raise ValueError("baseline_billed_cost must be non-negative")
        rec["baseline_billed_cost"] = baseline_cost
        rec["baseline_currency"] = baseline_cost_currency
    return _append_record(Path(path), rec)


def read_outcomes(path: Path = EVAL_LOG) -> list[dict]:
    ledger_path = Path(path)
    with _exclusive_log_lock(ledger_path):
        records = _strict_records(ledger_path)
    return [
        item
        for item in records
        if item.get("schema")
        not in {
            BUDGET_RESERVATION_SCHEMA,
            NO_PROVIDER_SETTLEMENT_SCHEMA,
            PROVIDER_CALL_START_SCHEMA,
        }
    ]


# ---------- objective judge ----------

def judge_outcome(rec: dict) -> str:
    """객관 신호로 under-route 판정: ok | escalate. LLM-judge 아님(순환 회피).

    escalate = 명확한 실패(error/cap/max_tokens) 또는 나쁜 outcome(rejected/needs-changes/
    gate-error/recurrence/reopen). 'length' 는 outcome 도 나쁠 때만(성공한 긴 출력 false-positive
    방지, reviewer #1). over-route(불필요하게 비쌈)는 report 의 opus_by_grade 가 본다.
    """
    finish = str(rec.get("finish_reason", "")).lower()
    outcome = str(rec.get("outcome", "")).lower()
    if finish in ESCALATION_FINISH:
        return "escalate"
    if finish == "length" and outcome not in NEUTRAL_OUTCOME:
        return "escalate"
    if outcome in ESCALATION_OUTCOME:
        return "escalate"
    return "ok"


# ---------- report (scoreboard) ----------

def _verified_baseline_receipt(
    rec: dict,
    receipt_index: dict[str, dict],
) -> tuple[dict | None, str | None]:
    if rec.get("schema") != EXECUTION_RECEIPT_SCHEMA:
        return None, "immutable_execution_receipt_required"
    baseline_id = str(rec.get("baseline_receipt_id") or "").strip()
    if not baseline_id:
        return None, "baseline_receipt_unavailable"
    baseline = receipt_index.get(baseline_id)
    if baseline is None or baseline is rec:
        return None, "baseline_receipt_unavailable"
    workload_id = str(rec.get("workload_id") or "").strip()
    if (
        not workload_id
        or str(baseline.get("workload_id") or "").strip() != workload_id
    ):
        return None, "workload_identity_mismatch"
    if not _execution_succeeded(baseline):
        return None, "baseline_execution_not_successful"
    if (
        not str(baseline.get("observed_model") or "").strip()
        or not _has_authoritative_token_usage(baseline)
    ):
        return None, "baseline_observation_unavailable"
    if not _route_observation_complete(baseline):
        return None, "baseline_reasoning_observation_unavailable"
    if rec.get("baseline_reference_status") != "verified":
        return None, "baseline_reference_unverified"
    return baseline, None


def _routing_evidence_exclusion_reason(
    rec: dict,
    receipt_index: dict[str, dict],
) -> str | None:
    baseline, baseline_reason = _verified_baseline_receipt(
        rec,
        receipt_index,
    )
    if baseline_reason:
        return baseline_reason
    if not _execution_succeeded(rec):
        return "actual_execution_not_successful"
    if not str(rec.get("observed_model") or "").strip():
        return "observed_model_unavailable"
    if not _route_observation_complete(rec):
        return "observed_reasoning_unavailable"
    if not str(rec.get("baseline_model") or "").strip():
        return "baseline_model_unavailable"
    actual_identity = (
        str(rec.get("observed_model") or "").strip(),
        str(rec.get("observed_reasoning_effort") or "").strip().lower()
        or None,
    )
    baseline_identity = (
        str((baseline or {}).get("observed_model") or "").strip(),
        str(
            (baseline or {}).get("observed_reasoning_effort") or ""
        ).strip().lower()
        or None,
    )
    if actual_identity == baseline_identity:
        return "route_ineffective_equivalent"
    if rec.get("application_status") != "applied":
        return "route_not_applied"
    changed = rec.get("route_changed")
    if changed is not True:
        if rec.get("route_status") == "ineffective_equivalent":
            return "route_ineffective_equivalent"
        return "route_change_unverified"
    if rec.get("route_status") != "effective":
        return "route_not_effective"
    return None


def _token_delta_exclusion_reason(
    rec: dict,
    receipt_index: dict[str, dict],
) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec, receipt_index)
    if routing_reason:
        return routing_reason
    if not _has_authoritative_token_usage(rec):
        return "actual_token_usage_unavailable"
    if int(rec.get("tokens", 0) or 0) <= 0:
        return "actual_token_usage_not_positive"
    baseline, _ = _verified_baseline_receipt(rec, receipt_index)
    if baseline is None or int(baseline.get("tokens", 0) or 0) <= 0:
        return "baseline_token_usage_unavailable"
    return None


def _monetary_delta_exclusion_reason(
    rec: dict,
    receipt_index: dict[str, dict],
) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec, receipt_index)
    if routing_reason:
        return routing_reason
    if not _has_authoritative_billed_cost(rec):
        return "actual_billed_cost_unavailable"
    baseline, _ = _verified_baseline_receipt(rec, receipt_index)
    if baseline is None:
        return "baseline_billed_cost_unavailable"
    if (
        not _has_authoritative_billed_cost(baseline)
    ):
        return "baseline_billed_cost_unavailable"
    if str(rec["currency"]).upper() != str(baseline["currency"]).upper():
        return "currency_mismatch"
    return None


def _exclusion_counts(records: list[dict], reason_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in records:
        reason = reason_fn(rec)
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _economic_claim_candidates(records: list[dict]) -> list[dict]:
    """Return rows that purport to compare an actual route with a baseline.

    A standalone baseline execution is evidence, not itself a failed savings
    claim, so it is intentionally absent from the exclusion denominator.
    """
    candidates: list[dict] = []
    for record in records:
        if record.get("schema") == EXECUTION_RECEIPT_SCHEMA:
            if (
                record.get("baseline_receipt_id")
                or record.get("route_changed") is not None
                or record.get("application_status") is not None
            ):
                candidates.append(record)
            continue
        if any(
            record.get(key) is not None
            for key in (
                "baseline_tokens",
                "baseline_model",
                "baseline_billed_cost",
                "model_changed",
                "route_status",
                "application_status",
            )
        ):
            candidates.append(record)
    return candidates


def report(records: list[dict] | None = None) -> dict:
    records = read_outcomes() if records is None else records
    receipt_index = {
        str(record.get("receipt_id")): record
        for record in records
        if record.get("schema") == EXECUTION_RECEIPT_SCHEMA
        and str(record.get("receipt_id") or "").strip()
    }
    by_grade: dict[str, dict] = {}
    by_model: dict[str, dict] = {}
    for r in records:
        verdict = judge_outcome(r)
        g = by_grade.setdefault(r.get("grade", "?"), {"count": 0, "tokens": 0, "escalations": 0})
        g["count"] += 1
        g["tokens"] += int(r.get("tokens", 0))
        g["escalations"] += 1 if verdict == "escalate" else 0
        m = by_model.setdefault(r.get("model", "?"), {"count": 0, "tokens": 0, "escalations": 0})
        m["count"] += 1
        m["tokens"] += int(r.get("tokens", 0))
        m["escalations"] += 1 if verdict == "escalate" else 0
    for d in (*by_grade.values(), *by_model.values()):
        d["escalation_rate"] = round(d["escalations"] / d["count"], 3) if d["count"] else 0.0
    # 등급별 opus 비율 — over-route baseline(reviewer #2): TASK-239 가 줄여야 할 숫자.
    # (전체 opus_share 는 "라우팅 전이라 다 opus"와 "정당하게 opus"를 구분 못 함.)
    opus_by_grade: dict[str, dict] = {}
    for r in records:
        g = opus_by_grade.setdefault(r.get("grade", "?"), {"opus": 0, "total": 0})
        g["total"] += 1
        g["opus"] += 1 if "opus" in str(r.get("model", "")).lower() else 0
    for g in opus_by_grade.values():
        g["opus_share"] = round(g["opus"] / g["total"], 3) if g["total"] else 0.0
    total = len(records)
    opus = sum(1 for r in records if "opus" in str(r.get("model", "")).lower())
    token_reason = lambda record: _token_delta_exclusion_reason(  # noqa: E731
        record,
        receipt_index,
    )
    economic_candidates = _economic_claim_candidates(records)
    delta_records = [
        r for r in economic_candidates if token_reason(r) is None
    ]
    actual_tokens = sum(int(r.get("tokens", 0) or 0) for r in delta_records)
    baseline_tokens = sum(
        int(
            receipt_index[str(r["baseline_receipt_id"])].get("tokens", 0)
            or 0
        )
        for r in delta_records
    )
    saved_tokens = baseline_tokens - actual_tokens
    token_delta = {
        "evidence_type": "token_usage",
        "monetary_claim": False,
        "eligible_records": len(delta_records),
        "excluded_records": len(economic_candidates) - len(delta_records),
        "exclusion_reasons": _exclusion_counts(
            economic_candidates,
            token_reason,
        ),
        "actual_tokens": actual_tokens,
        "baseline_tokens": baseline_tokens,
        "saved_tokens": saved_tokens,
        "saved_rate": round(saved_tokens / baseline_tokens, 3) if baseline_tokens else 0.0,
    }
    # Compatibility only: callers should migrate to token_delta.  The payload
    # explicitly says that token evidence is not a monetary cost claim.
    cost_delta = {
        **token_delta,
        "deprecated_alias": True,
        "label": "token delta (not monetary cost)",
    }
    monetary_reason = lambda record: _monetary_delta_exclusion_reason(  # noqa: E731
        record,
        receipt_index,
    )
    monetary_records = [
        r for r in economic_candidates if monetary_reason(r) is None
    ]
    monetary_by_currency: dict[str, dict] = {}
    for rec in monetary_records:
        currency = str(rec["currency"]).upper()
        bucket = monetary_by_currency.setdefault(
            currency,
            {
                "records": 0,
                "actual_billed_cost": 0.0,
                "baseline_billed_cost": 0.0,
            },
        )
        bucket["records"] += 1
        bucket["actual_billed_cost"] += float(rec["billed_cost"])
        baseline = receipt_index[str(rec["baseline_receipt_id"])]
        bucket["baseline_billed_cost"] += float(baseline["billed_cost"])
    for bucket in monetary_by_currency.values():
        bucket["saved_billed_cost"] = round(
            bucket["baseline_billed_cost"] - bucket["actual_billed_cost"],
            9,
        )
        baseline_cost = bucket["baseline_billed_cost"]
        bucket["saved_rate"] = (
            round(bucket["saved_billed_cost"] / baseline_cost, 3)
            if baseline_cost
            else 0.0
        )
        bucket["actual_billed_cost"] = round(bucket["actual_billed_cost"], 9)
        bucket["baseline_billed_cost"] = round(
            bucket["baseline_billed_cost"], 9
        )
    monetary_delta = {
        "evidence_type": "provider_billed_cost",
        "verified": bool(monetary_records),
        "eligible_records": len(monetary_records),
        "excluded_records": len(economic_candidates) - len(monetary_records),
        "exclusion_reasons": _exclusion_counts(
            economic_candidates, monetary_reason
        ),
        "by_currency": dict(sorted(monetary_by_currency.items())),
    }
    collab_records = [
        r for r in records
        if r.get("baseline_verdict") is not None
        and r.get("collab_verdict") is not None
        and r.get("collab_members")
        and int(r.get("baseline_tokens", 0) or 0) > 0
    ]
    collaboration_tokens = sum(int(r.get("tokens", 0) or 0) for r in collab_records)
    collaboration_baseline_tokens = sum(int(r.get("baseline_tokens", 0) or 0) for r in collab_records)
    verdict_changes = sum(
        1 for r in collab_records
        if str(r.get("baseline_verdict")) != str(r.get("collab_verdict"))
    )
    collaboration_delta = {
        "total": len(collab_records),
        "verdict_changes": verdict_changes,
        "verdict_change_rate": round(verdict_changes / len(collab_records), 3) if collab_records else 0.0,
        "baseline_tokens": collaboration_baseline_tokens,
        "collaboration_tokens": collaboration_tokens,
        "token_multiplier": (
            round(collaboration_tokens / collaboration_baseline_tokens, 3)
            if collaboration_baseline_tokens else 0.0
        ),
    }
    return {"total": total, "opus_share": round(opus / total, 3) if total else 0.0,
            "by_grade": by_grade, "by_model": by_model, "opus_by_grade": opus_by_grade,
            "token_delta": token_delta, "cost_delta": cost_delta,
            "monetary_delta": monetary_delta,
            "collaboration_delta": collaboration_delta}


def load_golden(path: Path = GOLDEN) -> list[dict]:
    return read_outcomes(path)


# ---------- escalation report (자가개선 제안 — 배치, 사람 ratify) ----------

def escalation_proposals(records: list[dict] | None = None, threshold: float = 0.3) -> list[str]:
    """grade 별 escalation율이 threshold 초과면 라우팅표 상향 제안(자동 적용 X — 사람 ratify)."""
    rep = report(records)
    props = []
    for grade, d in rep["by_grade"].items():
        if d["count"] >= 3 and d["escalation_rate"] > threshold:
            props.append(f"{grade}: escalation {d['escalations']}/{d['count']} "
                         f"({d['escalation_rate']}) > {threshold} → 상위 tier 라우팅 제안(사람 ratify)")
    for model, d in rep["by_model"].items():
        if d["count"] >= 3 and d["escalation_rate"] > threshold:
            props.append(f"{model}: escalation {d['escalations']}/{d['count']} "
                         f"({d['escalation_rate']}) > {threshold} → 모델 tier 재검토 제안(사람 ratify)")
    return props


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="agentic 측정 substrate (TASK-238)")
    ap.add_argument("--record", action="store_true", help="outcome/cost 로그 1건 기록")
    ap.add_argument("--report", action="store_true", help="스코어보드 출력")
    ap.add_argument("--proposals", action="store_true", help="라우팅 상향 제안(사람 ratify)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--log", type=Path, default=EVAL_LOG, help="eval 로그 경로(default: eval_log.jsonl)")
    ap.add_argument("--task-id")
    ap.add_argument("--grade")
    ap.add_argument("--model")
    ap.add_argument("--tokens", type=int)
    ap.add_argument("--finish-reason", default="stop")
    ap.add_argument("--outcome", default="ok")
    ap.add_argument("--policy-model")
    ap.add_argument("--selected-model")
    ap.add_argument("--routing-signal", action="append", default=[])
    ap.add_argument("--baseline-tokens", type=int)
    ap.add_argument("--actual-tokens-unknown", action="store_true",
                    help="mark tokens unknown so token_delta excludes this record")
    ap.add_argument("--provider")
    ap.add_argument("--requested-tier")
    ap.add_argument("--resolved-model")
    ap.add_argument("--observed-model")
    ap.add_argument("--model-changed", action="store_true")
    ap.add_argument("--route-status")
    ap.add_argument("--application-status")
    ap.add_argument("--baseline-model")
    ap.add_argument("--billed-cost", type=float)
    ap.add_argument("--currency")
    ap.add_argument("--baseline-billed-cost", type=float)
    ap.add_argument("--baseline-currency")
    ap.add_argument("--baseline-verdict")
    ap.add_argument("--collab-verdict")
    ap.add_argument("--collab-member", action="append", default=[])
    args = ap.parse_args(argv)
    if args.record:
        missing = [name for name in ("task_id", "grade", "model", "tokens") if getattr(args, name) in (None, "")]
        if missing:
            ap.error("--record requires " + ", ".join("--" + m.replace("_", "-") for m in missing))
        rec = record_outcome(
            args.task_id,
            args.grade,
            args.model,
            args.tokens,
            finish_reason=args.finish_reason,
            outcome=args.outcome,
            path=args.log,
            policy_model=args.policy_model,
            selected_model=args.selected_model,
            routing_signals=args.routing_signal or None,
            baseline_tokens=args.baseline_tokens,
            actual_tokens_known=False if args.actual_tokens_unknown else None,
            baseline_verdict=args.baseline_verdict,
            collab_verdict=args.collab_verdict,
            collab_members=args.collab_member or None,
            provider=args.provider,
            requested_tier=args.requested_tier,
            resolved_model=args.resolved_model,
            observed_model=args.observed_model,
            model_changed=True if args.model_changed else None,
            route_status=args.route_status,
            application_status=args.application_status,
            baseline_model=args.baseline_model,
            billed_cost=args.billed_cost,
            currency=args.currency,
            baseline_billed_cost=args.baseline_billed_cost,
            baseline_currency=args.baseline_currency,
        )
        print(json.dumps(rec, ensure_ascii=False, indent=2) if args.json else
              f"[eval] recorded {rec['task_id']} {rec['grade']} {rec['model']} {rec['tokens']} tokens")
        return 0
    if args.proposals:
        props = escalation_proposals()
        print(json.dumps(props, ensure_ascii=False, indent=2) if args.json else
              ("\n".join("  " + p for p in props) or "  (제안 없음)"))
        return 0
    rep = report()
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else
          f"[eval] total={rep['total']} opus_share={rep['opus_share']} "
          f"grades={ {g: d['escalation_rate'] for g, d in rep['by_grade'].items()} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
