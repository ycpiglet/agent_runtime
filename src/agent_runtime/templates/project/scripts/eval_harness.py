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
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_LOG = ROOT / "eval_log.jsonl"                       # gitignore (런타임)
GOLDEN = ROOT / "agents" / "lead_engineer" / "eval" / "golden.jsonl"  # committed fixture

# 객관 escalation 신호(model 이 약했거나 task 가 컸다 — under-route).
# 'length' 는 ambiguous(성공한 긴 출력일 수 있음) → outcome 도 나쁠 때만 escalate(reviewer #1).
ESCALATION_FINISH = {"error", "cap", "cap-hit", "max_tokens"}
ESCALATION_OUTCOME = {"rejected", "needs-changes", "gate-error", "recurrence", "reopen"}
NEUTRAL_OUTCOME = {"ok", "completed", ""}
MODEL_TIER = {"haiku": 1, "sonnet": 2, "opus": 3}       # 싼→비싼 (TASK-239 over-route 판정용)

EXECUTION_RECEIPT_SCHEMA = "agent-runtime-execution-receipt/v1"
RECEIPT_LOCK_TIMEOUT_SECONDS = 5.0

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
    return records


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
            str(item.get("dispatch_id") or "") == unique_dispatch_id
            for item in records
        ):
            raise ReceiptConflictError(
                f"immutable receipt already exists for dispatch_id={unique_dispatch_id}"
            )
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
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


def cumulative_usage(
    *,
    path: Path = EVAL_LOG,
    task_id: str,
    claim_id: str | None = None,
) -> dict:
    """Read durable observed usage for one task and optional claim."""
    records = _strict_records(Path(path))
    task_records = [
        item
        for item in records
        if item.get("schema") == EXECUTION_RECEIPT_SCHEMA
        and str(item.get("task_id") or "") == str(task_id)
    ]
    claim_records = (
        [
            item
            for item in task_records
            if str(item.get("claim_id") or "") == str(claim_id)
        ]
        if claim_id
        else []
    )

    def _usage(rows: list[dict]) -> dict:
        costs: dict[str, float] = {}
        tokens = 0
        for item in rows:
            tokens += max(0, int(item.get("tokens", 0) or 0))
            if (
                item.get("billed_cost_status") == "observed"
                and item.get("billed_cost") is not None
                and str(item.get("currency") or "").strip()
            ):
                currency = str(item["currency"]).upper()
                costs[currency] = costs.get(currency, 0.0) + float(
                    item["billed_cost"]
                )
        return {
            "receipts": len(rows),
            "tokens": tokens,
            "billed_cost_by_currency": {
                key: round(value, 9) for key, value in sorted(costs.items())
            },
        }

    return {
        "task_id": str(task_id),
        "claim_id": str(claim_id or "") or None,
        "task": _usage(task_records),
        "claim": _usage(claim_records),
    }


def budget_preflight(
    *,
    path: Path = EVAL_LOG,
    task_id: str,
    claim_id: str | None,
    dispatch_id: str,
    dispatch_ceiling: int | None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
) -> dict:
    """Fail closed before a provider call using durable cumulative receipts."""
    records = _strict_records(Path(path))
    if any(
        str(item.get("dispatch_id") or "") == str(dispatch_id)
        for item in records
    ):
        return {
            "allowed": False,
            "reason": "duplicate_dispatch_id",
            "dispatch_id": str(dispatch_id),
        }
    task_configured = task_token_budget not in (None, "")
    claim_configured = claim_token_budget not in (None, "")
    task_limit = _optional_nonnegative_int(task_token_budget)
    claim_limit = _optional_nonnegative_int(claim_token_budget)
    if task_configured and task_limit is None:
        return {
            "allowed": False,
            "reason": "invalid_task_token_budget",
            "dispatch_id": str(dispatch_id),
        }
    if claim_configured and claim_limit is None:
        return {
            "allowed": False,
            "reason": "invalid_claim_token_budget",
            "dispatch_id": str(dispatch_id),
        }
    ceiling = _optional_positive_int(dispatch_ceiling)
    configured = task_configured or claim_configured
    if configured and ceiling is None:
        return {
            "allowed": False,
            "reason": "dispatch_ceiling_unavailable",
            "dispatch_id": str(dispatch_id),
            "task_token_budget": task_limit,
            "claim_token_budget": claim_limit,
        }
    usage = cumulative_usage(
        path=Path(path),
        task_id=str(task_id),
        claim_id=str(claim_id or "") or None,
    )
    task_used = int(usage["task"]["tokens"])
    claim_used = int(usage["claim"]["tokens"])
    if task_limit is not None and task_used + int(ceiling or 0) > task_limit:
        reason = "task_budget_insufficient"
        allowed = False
    elif claim_limit is not None and claim_used + int(ceiling or 0) > claim_limit:
        reason = "claim_budget_insufficient"
        allowed = False
    else:
        reason = "within_budget"
        allowed = True
    return {
        "allowed": allowed,
        "reason": reason,
        "dispatch_id": str(dispatch_id),
        "dispatch_ceiling": ceiling,
        "task_token_budget": task_limit,
        "task_tokens_used": task_used,
        "task_tokens_remaining": (
            max(0, task_limit - task_used) if task_limit is not None else None
        ),
        "claim_token_budget": claim_limit,
        "claim_tokens_used": claim_used,
        "claim_tokens_remaining": (
            max(0, claim_limit - claim_used) if claim_limit is not None else None
        ),
    }


def record_execution_receipt(
    *,
    dispatch_id: str,
    task_id: str,
    source: str,
    status: str,
    claim_id: str | None = None,
    role: str | None = None,
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
    finish_reason: str = "stop",
    error: str | None = None,
    route_status: str | None = None,
    application_status: str | None = None,
    model_changed: bool | None = None,
    route_changed: bool | None = None,
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
        "finish_reason": str(finish_reason or "stop"),
        "outcome": "ok" if not error else "gate-error",
        "error": str(error or "").strip() or None,
        "route_status": route_status,
        "application_status": application_status,
        "model_changed": model_changed,
        "route_changed": route_changed,
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
    return _append_record(
        Path(path),
        rec,
        unique_dispatch_id=dispatch,
    )


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
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


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

def _routing_evidence_exclusion_reason(rec: dict) -> str | None:
    if not str(rec.get("observed_model") or "").strip():
        return "observed_model_unavailable"
    if not str(rec.get("baseline_model") or "").strip():
        return "baseline_model_unavailable"
    if (
        rec.get("schema") == EXECUTION_RECEIPT_SCHEMA
        and rec.get("baseline_observation_status") != "observed"
    ):
        return "baseline_observation_unavailable"
    if rec.get("application_status") != "applied":
        return "route_not_applied"
    changed = (
        rec.get("route_changed")
        if rec.get("schema") == EXECUTION_RECEIPT_SCHEMA
        else rec.get("model_changed")
    )
    if changed is not True:
        if rec.get("route_status") == "ineffective_equivalent":
            return "route_ineffective_equivalent"
        return "route_change_unverified"
    if rec.get("route_status") != "effective":
        return "route_not_effective"
    return None


def _token_delta_exclusion_reason(rec: dict) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec)
    if routing_reason:
        return routing_reason
    if rec.get("actual_tokens_known") is not True:
        return "actual_token_usage_unavailable"
    if int(rec.get("tokens", 0) or 0) <= 0:
        return "actual_token_usage_not_positive"
    if int(rec.get("baseline_tokens", 0) or 0) <= 0:
        return "baseline_token_usage_unavailable"
    return None


def _monetary_delta_exclusion_reason(rec: dict) -> str | None:
    routing_reason = _routing_evidence_exclusion_reason(rec)
    if routing_reason:
        return routing_reason
    if rec.get("billed_cost") is None or not str(rec.get("currency") or "").strip():
        return "actual_billed_cost_unavailable"
    if (
        rec.get("baseline_billed_cost") is None
        or not str(rec.get("baseline_currency") or "").strip()
    ):
        return "baseline_billed_cost_unavailable"
    if str(rec["currency"]).upper() != str(rec["baseline_currency"]).upper():
        return "currency_mismatch"
    return None


def _exclusion_counts(records: list[dict], reason_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in records:
        reason = reason_fn(rec)
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def report(records: list[dict] | None = None) -> dict:
    records = read_outcomes() if records is None else records
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
    delta_records = [r for r in records if _token_delta_exclusion_reason(r) is None]
    actual_tokens = sum(int(r.get("tokens", 0) or 0) for r in delta_records)
    baseline_tokens = sum(int(r.get("baseline_tokens", 0) or 0) for r in delta_records)
    saved_tokens = baseline_tokens - actual_tokens
    token_delta = {
        "evidence_type": "token_usage",
        "monetary_claim": False,
        "eligible_records": len(delta_records),
        "excluded_records": len(records) - len(delta_records),
        "exclusion_reasons": _exclusion_counts(records, _token_delta_exclusion_reason),
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
    monetary_records = [
        r for r in records if _monetary_delta_exclusion_reason(r) is None
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
        bucket["baseline_billed_cost"] += float(rec["baseline_billed_cost"])
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
        "excluded_records": len(records) - len(monetary_records),
        "exclusion_reasons": _exclusion_counts(
            records, _monetary_delta_exclusion_reason
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
